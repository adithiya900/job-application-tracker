from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from extensions import db
from models.job import ApplicationStatus, JobApplication
from seed import seed_database
from services.digest_service import send_weekly_digest
from services.reminder_service import send_interview_reminders


def test_validation_and_http_errors_use_documented_error_shape(client, auth_headers):
    missing_company = client.post("/api/applications", json={"role": "Engineer"}, headers=auth_headers)
    future_date = client.post(
        "/api/applications",
        json={"company": "Acme", "role": "Engineer", "applied_date": "2999-01-01"},
        headers=auth_headers,
    )
    invalid_json = client.post("/api/applications", data="{", content_type="application/json", headers=auth_headers)
    missing_route = client.get("/does-not-exist")

    for response in (missing_company, future_date, invalid_json, missing_route):
        payload = response.get_json()
        assert response.status_code >= 400
        assert set(("error", "details", "status_code")).issubset(payload)
        assert payload["status_code"] == response.status_code

    assert "company" in missing_company.get_json()["details"]
    assert "applied_date" in future_date.get_json()["details"]


def test_resume_upload_file_url_and_delete_cascade(client, auth_headers, test_user):
    application = JobApplication(
        company="File Company", role="Engineer", status=ApplicationStatus.APPLIED, user_id=test_user.id
    )
    db.session.add(application)
    db.session.commit()

    upload = client.post(
        f"/api/applications/{application.id}/resume",
        data={"resume": (BytesIO(b"%PDF-1.4\nresume"), "resume.pdf")},
        headers=auth_headers,
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    stored_path = Path(upload.get_json()["resume_path"])
    assert stored_path.is_file()

    served = client.get(f"/files/{stored_path.name}", headers=auth_headers)
    assert served.status_code == 200
    assert served.data.startswith(b"%PDF")
    served.close()

    deleted = client.delete(f"/api/applications/{application.id}", headers=auth_headers)
    assert deleted.status_code == 200
    assert not stored_path.exists()


def test_resume_text_returns_extracted_skills(client, auth_headers, test_user):
    application = JobApplication(
        company="Skills Company", role="Engineer", status=ApplicationStatus.APPLIED, user_id=test_user.id
    )
    db.session.add(application)
    db.session.commit()
    file_path = Path("uploads") / f"{application.id}_skills.pdf"
    file_path.parent.mkdir(exist_ok=True)
    file_path.write_bytes(b"%PDF-1.4\nresume")
    application.resume_path = str(file_path.resolve())
    db.session.commit()

    page = MagicMock()
    page.extract_text.return_value = "Python Flask SQL Docker"
    reader = MagicMock(pages=[page])
    with patch("api.jobs.PdfReader", return_value=reader):
        response = client.get(f"/api/applications/{application.id}/resume/text", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()["skills"] == ["Python", "SQL", "Flask", "Docker"]
    file_path.unlink(missing_ok=True)


def test_seed_database_creates_exactly_three_idempotently(test_app):
    assert seed_database() == 3
    assert JobApplication.query.count() == 3
    assert seed_database() == 0
    assert JobApplication.query.count() == 3


def test_digest_and_interview_reminder_render_and_send(test_app, test_user):
    now = datetime.utcnow().replace(microsecond=0)
    application = JobApplication(
        company="Mail Company",
        role="Engineer",
        status=ApplicationStatus.INTERVIEW,
        updated_at=now,
        interview_at=now + timedelta(hours=24),
        user_id=test_user.id,
    )
    db.session.add(application)
    db.session.commit()

    with patch("services.digest_service.send_template_email", return_value=True) as digest_sender:
        assert send_weekly_digest(test_user.id, now=now) is True
    assert digest_sender.call_args.kwargs["template_name"] == "emails/weekly_digest.html"
    assert "Mail Company" in digest_sender.call_args.kwargs["body"]

    with patch("services.reminder_service.send_template_email", return_value=True) as reminder_sender:
        assert send_interview_reminders(now=now) == 1
    assert reminder_sender.call_args.kwargs["template_name"] == "emails/interview_reminder.html"
    assert application.interview_reminder_sent_at == now
