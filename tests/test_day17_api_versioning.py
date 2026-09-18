from pathlib import Path

from flask_jwt_extended import create_access_token


def test_v1_applications_is_deprecated(test_app):
    client = test_app.test_client()

    response = client.get("/api/v1/applications")

    assert response.status_code == 401
    assert response.headers.get("Deprecation") == "true"


def test_v2_applications_route_exists(test_app):
    with test_app.app_context():
        token = create_access_token(identity="1")

    client = test_app.test_client()

    response = client.get(
        "/api/v2/applications",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


def test_v2_summary_format(test_app):
    with test_app.app_context():
        token = create_access_token(identity="1")

    client = test_app.test_client()

    response = client.get(
        "/api/v2/applications?format=summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "applications" in data
    assert "pagination" in data

    for application in data["applications"]:
        assert set(application.keys()) == {
            "id",
            "company",
            "role",
            "status",
        }


def test_day17_documentation_files_exist():
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "Changelog.md").exists()
    assert (project_root / "MIGRATION_V1_TO_V2.md").exists()
    