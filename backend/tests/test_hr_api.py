"""
Tests for HR API endpoints and Candidate-HR workflow
===================================================
"""

import pytest
from extensions import db, bcrypt
from models.user import User, Role
from models.job import JobApplication, ApplicationStatus, ApplicationStatusHistory


@pytest.fixture
def hr_user(test_app):
    user = User(
        name="HR Recruiter",
        email="hr@company.com",
        role=Role.HR,
        password=bcrypt.generate_password_hash("hrpassword123").decode("utf-8")
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def hr_token(client, hr_user):
    res = client.post("/login", json={
        "email": hr_user.email,
        "password": "hrpassword123"
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
