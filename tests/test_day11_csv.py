import csv
from datetime import date
from io import BytesIO, StringIO

from flask_jwt_extended import create_access_token

from extensions import db
from models.job import ApplicationStatus, JobApplication


CSV_HEADERS = [
    "id",
    "company",
    "role",
    "status",
    "applied_date",
    "interview_at",
    "notes",
]


def csv_upload(content):
    return {
        "file": (BytesIO(content.encode("utf-8")), "applications.csv")
    }


def test_csv_export_is_authenticated_and_user_scoped(client, test_user):
    application = JobApplication(
        company="Owned Company",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=test_user.id,
    )
    other_user_token = create_access_token(identity=str(test_user.id + 1))
    db.session.add(application)
    db.session.commit()

    response = client.get(
        "/applications/export",
        headers={
            "Authorization": f"Bearer {create_access_token(identity=str(test_user.id))}"
        },
    )

    assert response.status_code == 200
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert "Owned Company" in response.get_data(as_text=True)

    other_response = client.get(
        "/applications/export",
        headers={"Authorization": f"Bearer {other_user_token}"},
    )
    assert other_response.status_code == 200
    assert "Owned Company" not in other_response.get_data(as_text=True)


def test_csv_round_trip_updates_exported_rows_without_data_loss(
    client, auth_headers, test_user
):
    applications = [
        JobApplication(
            company=f"Company {index}",
            role=f"Role {index}",
            status=ApplicationStatus.APPLIED,
            applied_date=date(2026, 9, index),
            notes=f"Original {index}",
            user_id=test_user.id,
        )
        for index in (1, 2, 3, 4)
    ]
    db.session.add_all(applications)
    db.session.commit()

    exported = client.get("/applications/export", headers=auth_headers)
    rows = list(csv.DictReader(StringIO(exported.get_data(as_text=True))))
    for row in rows[:3]:
        row["status"] = "INTERVIEW"
        row["notes"] = f"Edited {row['id']}"

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    imported = client.post(
        "/applications/import",
        data=csv_upload(output.getvalue()),
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    assert imported.status_code == 200
    assert imported.get_json()["imported"] == 4
    assert imported.get_json()["failed"] == 0

    for row in rows[:3]:
        application = db.session.get(JobApplication, int(row["id"]))
        assert application.status == ApplicationStatus.INTERVIEW
        assert application.notes == f"Edited {row['id']}"
    unchanged = db.session.get(JobApplication, int(rows[3]["id"]))
    assert unchanged.status == ApplicationStatus.APPLIED
    assert unchanged.notes == "Original 1"


def test_csv_import_skips_invalid_rows_and_downloads_error_log(
    client, auth_headers, test_user
):
    valid = "newco,Engineer,APPLIED,2026-09-01,,Valid row\n"
    invalid = "badco,,NOT_A_STATUS,not-a-date,,Invalid row\n"
    content = "company,role,status,applied_date,interview_at,notes\n" + valid + invalid

    response = client.post(
        "/applications/import",
        data=csv_upload(content),
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["imported"] == 1
    assert data["failed"] == 1
    assert data["errors"][0]["data"]["company"] == "badco"
    assert JobApplication.query.filter_by(company="newco", user_id=test_user.id).count() == 1

    error_log = client.get("/applications/import/errors", headers=auth_headers)
    assert error_log.status_code == 200
    assert "Role is required" in error_log.get_data(as_text=True)
    assert "badco" in error_log.get_data(as_text=True)


def test_csv_import_rejects_missing_headers(client, auth_headers):
    response = client.post(
        "/applications/import",
        data=csv_upload("company,role\nAcme,Engineer\n"),
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "Missing required headers" in response.get_json()["error"]


def test_bulk_status_update_csv_validates_ids_and_statuses(
    client, auth_headers, test_user
):
    application = JobApplication(
        company="Status Company",
        role="Engineer",
        status=ApplicationStatus.APPLIED,
        user_id=test_user.id,
    )
    db.session.add(application)
    db.session.commit()

    content = (
        "id,status\n"
        f"{application.id},OFFER\n"
        "not-an-id,INTERVIEW\n"
        "99999,REJECTED\n"
    )
    response = client.post(
        "/applications/import",
        data=csv_upload(content),
        headers=auth_headers,
        content_type="multipart/form-data",
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["imported"] == 1
    assert data["failed"] == 2
    db.session.refresh(application)
    assert application.status == ApplicationStatus.OFFER
