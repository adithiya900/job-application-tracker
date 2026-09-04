import pytest
from datetime import date
from extensions import db
from models.job import JobApplication, ApplicationStatus
from services.application_service import ApplicationService


# ==========================================
# Day 8: PATCH /applications/<id> Tests
# ==========================================

def test_patch_application_api(client, auth_headers, test_application):
    """Test PATCH with multiple fields."""
    patch_data = {
        "role": "Lead Software Engineer",
        "notes": "Promoted during review"
    }

    response = client.patch(
        f"/applications/{test_application.id}",
        json=patch_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Application updated successfully!"
    assert data["application"]["role"] == "Lead Software Engineer"
    assert data["application"]["notes"] == "Promoted during review"
    # Unchanged fields remain preserved
    assert data["application"]["company"] == test_application.company


def test_patch_application_only_status(client, auth_headers, test_application):
    """Test PATCH partial update using only status."""
    patch_data = {
        "status": "OFFER"
    }

    response = client.patch(
        f"/applications/{test_application.id}",
        json=patch_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Application updated successfully!"
    assert data["application"]["status"] == "OFFER"
    # Verify other fields remain intact
    assert data["application"]["company"] == test_application.company
    assert data["application"]["role"] == test_application.role


def test_patch_application_only_notes(client, auth_headers, test_application):
    """Test PATCH partial update using only notes."""
    patch_data = {
        "notes": "Follow-up email sent to recruiter"
    }

    response = client.patch(
        f"/applications/{test_application.id}",
        json=patch_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Application updated successfully!"
    assert data["application"]["notes"] == "Follow-up email sent to recruiter"
    assert data["application"]["company"] == test_application.company


def test_patch_application_api_prefix(client, auth_headers, test_application):
    """Test PATCH /api/applications/<id>."""
    patch_data = {
        "notes": "Updated via /api/applications path"
    }

    response = client.patch(
        f"/api/applications/{test_application.id}",
        json=patch_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Application updated successfully!"
    assert data["application"]["notes"] == "Updated via /api/applications path"


def test_patch_application_not_found(client, auth_headers):
    """Test PATCH on non-existent application ID."""
    response = client.patch(
        "/applications/999999",
        json={"notes": "test"},
        headers=auth_headers
    )
    assert response.status_code == 404


# ==========================================
# Day 8: Pagination Response Headers Tests
# ==========================================

def test_get_applications_pagination_headers(client, auth_headers, test_user):
    """Verify pagination headers: X-Total-Count, X-Page, X-Per-Page, X-Total-Pages, X-Has-Next, X-Has-Prev."""
    for i in range(7):
        app = JobApplication(
            company=f"Company {i}",
            role=f"Role {i}",
            status=ApplicationStatus.APPLIED,
            user_id=test_user.id
        )
        db.session.add(app)
    db.session.commit()

    # Request page 1 with per_page=3
    response = client.get(
        "/applications?page=1&per_page=3",
        headers=auth_headers
    )

    assert response.status_code == 200
    headers = response.headers

    assert "X-Total-Count" in headers
    assert "X-Page" in headers
    assert "X-Per-Page" in headers
    assert "X-Total-Pages" in headers
    assert "X-Has-Next" in headers
    assert "X-Has-Prev" in headers

    assert headers["X-Total-Count"] == "7"
    assert headers["X-Page"] == "1"
    assert headers["X-Per-Page"] == "3"
    assert headers["X-Total-Pages"] == "3"
    assert headers["X-Has-Next"] == "true"
    assert headers["X-Has-Prev"] == "false"

    # Verify JSON pagination object is also still present
    data = response.get_json()
    assert "pagination" in data
    assert data["pagination"]["total"] == 7
    assert data["pagination"]["page"] == 1


# ==========================================
# Day 8: /api Route Aliases Tests
# ==========================================

def test_get_api_applications(client, auth_headers, test_application):
    """Test GET /api/applications."""
    response = client.get(
        "/api/applications",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "applications" in data
    assert len(data["applications"]) >= 1
    assert "X-Total-Count" in response.headers


def test_get_api_application_by_id(client, auth_headers, test_application):
    """Test GET /api/applications/<id>."""
    response = client.get(
        f"/api/applications/{test_application.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == test_application.id
    assert data["company"] == test_application.company


def test_post_api_applications(client, auth_headers):
    """Test POST /api/applications."""
    data = {
        "company": "Netflix New",
        "role": "Staff Engineer",
        "status": "APPLIED"
    }
    response = client.post(
        "/api/applications",
        json=data,
        headers=auth_headers
    )
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["application"]["company"] == "Netflix New"


# ==========================================
# Day 8: Statistics Endpoints Tests
# ==========================================

def test_get_applications_stats(client, auth_headers, test_user):
    """Test GET /applications/stats and verify phone_screen & by_status."""
    statuses = [
        ApplicationStatus.APPLIED,
        ApplicationStatus.PHONE_SCREEN,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED
    ]
    for idx, st in enumerate(statuses):
        app = JobApplication(
            company=f"Stats Company {idx}",
            role="Engineer",
            status=st,
            user_id=test_user.id
        )
        db.session.add(app)
    db.session.commit()

    response = client.get(
        "/applications/stats",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()

    assert data["total_applications"] == 5
    assert data["applied"] == 1
    assert data["phone_screen"] == 1
    assert data["interview"] == 1
    assert data["rejected"] == 1
    assert data["offered"] == 1

    assert "by_status" in data
    assert data["by_status"]["APPLIED"] == 1
    assert data["by_status"]["PHONE_SCREEN"] == 1
    assert data["by_status"]["INTERVIEW"] == 1
    assert data["by_status"]["OFFER"] == 1
    assert data["by_status"]["REJECTED"] == 1


def test_get_api_applications_stats(client, auth_headers, test_user):
    """Test GET /api/applications/stats."""
    response = client.get(
        "/api/applications/stats",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "total_applications" in data
    assert "by_status" in data


def test_get_stats_unauthorized(client):
    """Test GET /api/applications/stats without token returns 401."""
    response = client.get("/api/applications/stats")
    assert response.status_code == 401


# ==========================================
# Day 8: Service Update Applied Date Test
# ==========================================

def test_service_update_applied_date(test_app, test_user):
    """Test that update_application updates applied_date when supplied."""
    app = ApplicationService.create_application(
        {
            "company": "Apple",
            "role": "iOS Developer"
        },
        test_user.id
    )
    target_date = date(2026, 1, 15)
    updated = ApplicationService.update_application(
        app.id,
        {"applied_date": target_date},
        test_user.id
    )
    assert updated.applied_date == target_date
