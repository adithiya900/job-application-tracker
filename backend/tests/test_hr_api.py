"""
Tests for HR API endpoints and Candidate-HR workflow
==================================================
"""

import pytest
from extensions import db, bcrypt
from models.user import User, Role
from models.job import JobApplication, ApplicationStatus, ApplicationStatusHistory, InterviewDetail, InterviewFeedback


@pytest.fixture
def hr_user(test_app):
    user = User(
        name="HR Recruiter",
        email="hr@gmail.com",
        role=Role.HR,
        password=bcrypt.generate_password_hash("hr123").decode("utf-8")
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def hr_token(client, hr_user):
    res = client.post("/login", json={
        "email": hr_user.email,
        "password": "hr123"
    })
    assert res.status_code == 200
    return res.json["access_token"]


@pytest.fixture
def hr_headers(hr_token):
    return {"Authorization": f"Bearer {hr_token}"}


def test_candidate_hr_full_workflow(client, auth_headers, test_user, hr_headers, hr_user):
    """
    Test full lifecycle:
    1. Candidate submits application
    2. HR lists applications & sees candidate's application
    3. HR updates status to UNDER_REVIEW, then INTERVIEW
    4. HR schedules an interview
    5. HR submits interview feedback
    6. HR updates status to OFFER
    7. Candidate fetches application and verifies timeline history
    """
    # 1. Candidate creates job application
    app_data = {
        "company": "TechCorp Solutions",
        "role": "Senior Full Stack Engineer",
        "status": "APPLIED",
        "notes": "Applied via referral"
    }
    create_res = client.post("/api/applications", json=app_data, headers=auth_headers)
    assert create_res.status_code == 201
    app_id = create_res.json["application"]["id"]

    # 2. HR lists applications
    hr_list_res = client.get("/api/hr/applications", headers=hr_headers)
    assert hr_list_res.status_code == 200
    apps = hr_list_res.json["applications"]
    assert len(apps) >= 1
    target = next((a for a in apps if a["id"] == app_id), None)
    assert target is not None
    assert target["candidate"]["email"] == test_user.email

    candidate_search_res = client.get(
        "/api/hr/applications",
        query_string={"search": test_user.email},
        headers=hr_headers,
    )
    assert candidate_search_res.status_code == 200
    assert any(
        app["id"] == app_id
        for app in candidate_search_res.json["applications"]
    )

    # 3. HR updates status to UNDER_REVIEW
    status_res = client.patch(
        f"/api/hr/applications/{app_id}/status",
        json={"status": "UNDER_REVIEW", "notes": "Resume matches criteria"},
        headers=hr_headers
    )
    assert status_res.status_code == 200
    assert status_res.json["application"]["status"] == "UNDER_REVIEW"

    # HR updates status to INTERVIEW
    status_res2 = client.patch(
        f"/api/hr/applications/{app_id}/status",
        json={"status": "INTERVIEW", "notes": "Scheduling round 1"},
        headers=hr_headers
    )
    assert status_res2.status_code == 200

    # 4. HR schedules interview
    interview_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/xyz-abc-def",
            "interviewer": "Tech Lead John",
            "hr_notes": "Internal: Focus on System Design"
        },
        headers=hr_headers
    )
    assert interview_res.status_code == 200
    assert interview_res.json["interview"]["interview_round"] == "Technical Round 1"

    # 5. HR submits feedback
    feedback_res = client.post(
        f"/api/hr/applications/{app_id}/feedback",
        json={
            "technical_skills": "Excellent",
            "communication": "Very Good",
            "overall_feedback": "Strong candidate for senior role",
            "recommendation": "Hire",
            "internal_notes": "Comp range requested $130k"
        },
        headers=hr_headers
    )
    assert feedback_res.status_code == 201

    # 6. HR updates status to OFFER
    offer_res = client.patch(
        f"/api/hr/applications/{app_id}/status",
        json={"status": "OFFER", "notes": "Offer letter sent"},
        headers=hr_headers
    )
    assert offer_res.status_code == 200

    # 7. Candidate views application detail & history
    candidate_view = client.get(f"/api/applications/{app_id}", headers=auth_headers)
    assert candidate_view.status_code == 200
    c_data = candidate_view.json
    assert c_data["status"] == "OFFER"
    assert "status_history" in c_data
    history = c_data["status_history"]
    assert len(history) >= 4  # Initial APPLIED -> UNDER_REVIEW -> INTERVIEW -> OFFER
    assert history[-1]["new_status"] == "OFFER"


def test_candidate_cannot_access_hr_endpoints(client, auth_headers):
    """Ensure standard candidate cannot access HR endpoints."""
    res = client.get("/api/hr/applications", headers=auth_headers)
    assert res.status_code == 403


def test_disabled_candidate_blocks_hr_actions(client, hr_headers, test_app):
    """HR actions on disabled candidate applications must be rejected with 403."""
    admin = User(
        name="Admin User",
        email="admin-disabled@example.com",
        password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        role=Role.ADMIN,
    )
    candidate = User(
        name="Disabled Candidate",
        email="disabled-candidate@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    hr = User(
        name="HR User",
        email="hr-disabled@example.com",
        password=bcrypt.generate_password_hash("hr123").decode("utf-8"),
        role=Role.HR,
    )
    db.session.add_all([admin, candidate, hr])
    db.session.commit()

    application = JobApplication(
        company="Blocked Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()

    admin_token = client.post("/login", json={
        "email": admin.email,
        "password": "admin123"
    }).json["access_token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    # Disable candidate
    disable_res = client.patch(f"/api/admin/users/{candidate.id}", headers=admin_h, json={"is_active": False})
    assert disable_res.status_code == 200

    app_id = application.id
    original_status = application.status.value

    # Status update must be rejected
    status_res = client.patch(
        f"/api/hr/applications/{app_id}/status",
        headers=hr_headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert status_res.status_code == 403
    assert status_res.get_json()["error"] == "This candidate account is disabled. HR actions are not allowed."

    db.session.refresh(application)
    assert application.status.value == original_status

    # Interview scheduling must be rejected
    interview_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/abc",
        },
    )
    assert interview_res.status_code == 403
    assert interview_res.get_json()["error"] == "This candidate account is disabled. HR actions are not allowed."

    assert InterviewDetail.query.filter_by(application_id=app_id).count() == 0

    # Feedback must be rejected
    feedback_res = client.post(
        f"/api/hr/applications/{app_id}/feedback",
        headers=hr_headers,
        json={"technical_skills": "Good", "recommendation": "Hire"},
    )
    assert feedback_res.status_code == 403
    assert feedback_res.get_json()["error"] == "This candidate account is disabled. HR actions are not allowed."

    assert InterviewFeedback.query.filter_by(application_id=app_id).count() == 0


def test_re_enabled_candidate_allows_hr_actions(client, hr_headers, test_app):
    """After re-enabling candidate, HR actions should succeed."""
    admin = User(
        name="Admin User",
        email="admin-reenable@example.com",
        password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        role=Role.ADMIN,
    )
    candidate = User(
        name="Re-enabled Candidate",
        email="reenable-candidate@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    db.session.add_all([admin, candidate])
    db.session.commit()

    application = JobApplication(
        company="Re-enable Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()

    admin_token = client.post("/login", json={
        "email": admin.email,
        "password": "admin123"
    }).json["access_token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    # Disable then re-enable
    assert client.patch(f"/api/admin/users/{candidate.id}", headers=admin_h, json={"is_active": False}).status_code == 200
    assert client.patch(f"/api/admin/users/{candidate.id}", headers=admin_h, json={"is_active": True}).status_code == 200

    app_id = application.id
    status_res = client.patch(
        f"/api/hr/applications/{app_id}/status",
        headers=hr_headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert status_res.status_code == 200

    interview_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/abc",
        },
    )
    assert interview_res.status_code == 200


def test_google_meet_requires_meeting_link(client, hr_headers, test_app):
    """Google Meet / Online interviews must require a non-empty meeting link."""
    admin = User(
        name="Admin User",
        email="admin-meet@example.com",
        password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        role=Role.ADMIN,
    )
    candidate = User(
        name="Meet Candidate",
        email="meet-candidate@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
    )
    db.session.add_all([admin, candidate])
    db.session.commit()

    application = JobApplication(
        company="Meet Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()

    app_id = application.id

    # Empty link must fail
    empty_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "",
        },
    )
    assert empty_res.status_code == 400
    assert empty_res.get_json()["error"] == "Meeting link is required for Google Meet interviews."

    # Whitespace-only link must fail
    ws_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "   ",
        },
    )
    assert ws_res.status_code == 400
    assert ws_res.get_json()["error"] == "Meeting link is required for Google Meet interviews."

    # Valid link must succeed
    valid_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/abc-def-ghi",
        },
    )
    assert valid_res.status_code == 200
    assert valid_res.get_json()["interview"]["meeting_link"] == "https://meet.google.com/abc-def-ghi"

    # Switch to non-Online type must clear meeting link
    switch_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Phone Screen",
        },
    )
    assert switch_res.status_code == 200
    assert switch_res.get_json()["interview"]["meeting_link"] is None
    assert switch_res.get_json()["interview"]["interview_type"] == "Phone Screen"


def test_non_google_meet_does_not_expose_stale_link_to_candidate(client, test_app):
    """Candidate must not see a stale Google Meet link after type switch."""
    admin = User(
        name="Admin User",
        email="admin-stale@example.com",
        password=bcrypt.generate_password_hash("admin123").decode("utf-8"),
        role=Role.ADMIN,
    )
    hr = User(
        name="HR User",
        email="hr-stale@example.com",
        password=bcrypt.generate_password_hash("hr123").decode("utf-8"),
        role=Role.HR,
    )
    candidate = User(
        name="Stale Candidate",
        email="stale-candidate@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
    )
    db.session.add_all([admin, hr, candidate])
    db.session.commit()

    application = JobApplication(
        company="Stale Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()

    admin_token = client.post("/login", json={
        "email": admin.email,
        "password": "admin123"
    }).json["access_token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    hr_token = client.post("/login", json={
        "email": hr.email,
        "password": "hr123"
    }).json["access_token"]
    hr_h = {"Authorization": f"Bearer {hr_token}"}

    app_id = application.id

    # Set Google Meet link
    client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_h,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Online",
            "meeting_link": "https://meet.google.com/stale-link",
        },
    )

    # Switch to Phone Screen
    client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_h,
        json={
            "interview_date": "2026-10-15",
            "interview_time": "14:00",
            "interview_round": "Technical Round 1",
            "interview_type": "Phone Screen",
        },
    )

    cand_token = client.post("/login", json={
        "email": candidate.email,
        "password": "candidate123"
    }).json["access_token"]
    cand_h = {"Authorization": f"Bearer {cand_token}"}

    cand_view = client.get(f"/api/applications/{app_id}", headers=cand_h)
    assert cand_view.status_code == 200
    c_data = cand_view.json
    assert c_data["interview_details"] is not None
    assert isinstance(c_data["interview_details"], list)
    assert len(c_data["interview_details"]) == 2
    # The last interview (Phone Screen) should have no meeting link
    latest = c_data["interview_details"][-1]
    assert latest["meeting_link"] is None
    assert latest["interview_type"] == "Phone Screen"


def test_withdrawn_application_blocks_hr_actions(client, hr_headers, test_app):
    """
    A candidate-withdrawn application is closed: HR cannot change its status,
    schedule interviews, submit feedback or message the candidate.
    """
    candidate = User(
        name="Withdrawer",
        email="withdrawer@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    db.session.add(candidate)
    db.session.commit()

    application = JobApplication(
        company="Withdrawn Co",
        role="Designer",
        status=ApplicationStatus.WITHDRAWN,
        user_id=candidate.id,
    )
    db.session.add(application)
    db.session.commit()
    app_id = application.id

    expected = "This application was withdrawn by the candidate. No further actions are available."

    status_res = client.patch(
        f"/api/hr/applications/{app_id}/status",
        headers=hr_headers,
        json={"status": "UNDER_REVIEW"},
    )
    assert status_res.status_code == 403
    assert status_res.get_json()["error"] == expected

    interview_res = client.patch(
        f"/api/hr/applications/{app_id}/interview",
        headers=hr_headers,
        json={"interview_date": "2026-11-01", "interview_time": "10:00"},
    )
    assert interview_res.status_code == 403
    assert interview_res.get_json()["error"] == expected

    feedback_res = client.post(
        f"/api/hr/applications/{app_id}/feedback",
        headers=hr_headers,
        json={"feedback": "Strong portfolio"},
    )
    assert feedback_res.status_code == 403
    assert feedback_res.get_json()["error"] == expected

    notify_res = client.post(
        f"/api/hr/applications/{app_id}/notify",
        headers=hr_headers,
        json={"message": "We would like to interview you."},
    )
    assert notify_res.status_code == 403
    assert notify_res.get_json()["error"] == expected

    # Read-only views stay available so the row is still inspectable.
    assert client.get(f"/api/hr/applications/{app_id}", headers=hr_headers).status_code == 200


def test_withdrawn_application_is_skipped_in_bulk_status_update(client, hr_headers, test_app):
    """Bulk actions must not resurrect a withdrawn application."""
    candidate = User(
        name="Bulk Withdrawer",
        email="bulk-withdrawer@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    db.session.add(candidate)
    db.session.commit()

    withdrawn = JobApplication(
        company="Bulk Withdrawn Co",
        role="Engineer",
        status=ApplicationStatus.WITHDRAWN,
        user_id=candidate.id,
    )
    active = JobApplication(
        company="Bulk Active Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
    )
    db.session.add_all([withdrawn, active])
    db.session.commit()

    result = client.post(
        "/api/hr/applications/bulk",
        headers=hr_headers,
        json={
            "application_ids": [withdrawn.id, active.id],
            "action": "bulk_status_update",
            "status": "UNDER_REVIEW",
        },
    )
    assert result.status_code == 200

    payload = result.get_json()["results"]
    skipped = payload["skipped"]
    assert any(item["id"] == withdrawn.id and item["reason"] == "Application withdrawn" for item in skipped)

    db.session.refresh(withdrawn)
    assert withdrawn.status == ApplicationStatus.WITHDRAWN


def test_withdrawn_application_cannot_be_shortlisted(client, hr_headers, test_app):
    """Shortlisting is an action reserved for applications still in progress."""
    candidate = User(
        name="Shortlist Withdrawer",
        email="shortlist-withdrawer@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    db.session.add(candidate)
    db.session.commit()

    withdrawn = JobApplication(
        company="Shortlist Withdrawn Co",
        role="Engineer",
        status=ApplicationStatus.WITHDRAWN,
        user_id=candidate.id,
    )
    db.session.add(withdrawn)
    db.session.commit()

    response = client.patch(
        f"/api/hr/applications/{withdrawn.id}/shortlist",
        headers=hr_headers,
        json={},
    )
    assert response.status_code == 403
    assert response.get_json()["error"] == (
        "This application was withdrawn by the candidate. "
        "No further actions are available."
    )

    db.session.refresh(withdrawn)
    assert withdrawn.is_shortlisted in (False, None)


def test_hr_list_includes_shortlist_flag(client, hr_headers, test_app):
    """
    The HR serializer must return is_shortlisted so the shortlist state
    survives a page refresh instead of silently reverting.
    """
    candidate = User(
        name="Shortlist Flag",
        email="shortlist-flag@example.com",
        password=bcrypt.generate_password_hash("candidate123").decode("utf-8"),
        role=Role.USER,
        is_active=True,
    )
    db.session.add(candidate)
    db.session.commit()

    application = JobApplication(
        company="Flag Co",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=candidate.id,
        is_shortlisted=True,
    )
    db.session.add(application)
    db.session.commit()

    data = client.get("/api/hr/applications", headers=hr_headers).get_json()
    row = next(a for a in data["applications"] if a["id"] == application.id)
    assert row["is_shortlisted"] is True

    detail = client.get(f"/api/hr/applications/{application.id}", headers=hr_headers).get_json()
    assert detail["is_shortlisted"] is True
