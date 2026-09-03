import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from extensions import db
from models.job import JobApplication, ApplicationStatus


# ==========================================
# Create Application API
# ==========================================
def test_create_application_api(client, auth_headers):

    data = {
        "company": "Google",
        "role": "Software Engineer",
        "status": "APPLIED",
        "notes": "Applied through API test"
    }

    response = client.post(
        "/applications",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 201

    response_data = response.get_json()

    assert response_data["message"] == (
        "Application created successfully!"
    )

    assert response_data["application"]["company"] == "Google"
    assert response_data["application"]["role"] == "Software Engineer"
    assert response_data["application"]["status"] == "APPLIED"


# ==========================================
# Create Application - Missing Company
# ==========================================
def test_create_application_missing_company(
    client,
    auth_headers
):

    data = {
        "role": "Software Engineer"
    }

    response = client.post(
        "/applications",
        json=data,
        headers=auth_headers
    )

    assert response.status_code == 400

    assert response.get_json()["error"] == "Company is required"


# ==========================================
# Get All Applications API
# ==========================================
def test_get_all_applications_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Microsoft",
        role="Backend Developer",
        status=ApplicationStatus.APPLIED,
        notes="API test",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.get(
        "/applications",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "applications" in data
    assert "pagination" in data

    assert len(data["applications"]) == 1

    assert data["applications"][0]["company"] == "Microsoft"


# ==========================================
# Get Application By ID API
# ==========================================
def test_get_application_by_id_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Amazon",
        role="Python Developer",
        status=ApplicationStatus.INTERVIEW,
        notes="Interview round",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.get(
        f"/applications/{application.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["company"] == "Amazon"
    assert data["role"] == "Python Developer"
    assert data["status"] == "INTERVIEW"


# ==========================================
# Get Application Not Found API
# ==========================================
def test_get_application_not_found_api(
    client,
    auth_headers
):

    response = client.get(
        "/applications/99999",
        headers=auth_headers
    )

    assert response.status_code == 404


# ==========================================
# Update Application API
# ==========================================
def test_update_application_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Meta",
        role="Frontend Developer",
        status=ApplicationStatus.APPLIED,
        notes="Initial notes",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    updated_data = {
        "status": "INTERVIEW",
        "notes": "Interview scheduled"
    }

    response = client.put(
        f"/applications/{application.id}",
        json=updated_data,
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Application updated successfully!"
    )

    assert data["application"]["status"] == "INTERVIEW"
    assert data["application"]["notes"] == "Interview scheduled"


# ==========================================
# Delete Application API
# ==========================================
def test_delete_application_api(
    client,
    auth_headers,
    test_user
):

    application = JobApplication(
        company="Netflix",
        role="Software Developer",
        status=ApplicationStatus.APPLIED,
        notes="Delete API test",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    response = client.delete(
        f"/applications/{application.id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Application deleted successfully!"
    )

    deleted_application = db.session.get(
        JobApplication,
        application.id
    )

    assert deleted_application is None


# ==========================================
# Unauthorized Request
# ==========================================
def test_unauthorized_request(client):

    response = client.get("/applications")

    assert response.status_code == 401


# ==========================================
# Day 6 - Resume Upload Tests
# ==========================================

# ==========================================
# Upload Resume - Success
# ==========================================
def test_upload_resume_success(
    client,
    auth_headers,
    test_application
):

    fake_pdf = BytesIO(
        b"%PDF-1.4 fake pdf content"
    )

    response = client.post(
        f"/applications/{test_application.id}/resume",
        data={
            "resume": (
                fake_pdf,
                "resume.pdf"
            )
        },
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Resume uploaded successfully!"
    )

    assert data["resume_path"].endswith(".pdf")

    # Verify database was updated
    application = db.session.get(
        JobApplication,
        test_application.id
    )

    assert application.resume_path == data["resume_path"]


# ==========================================
# Upload Resume - File Required
# ==========================================
def test_upload_resume_required(
    client,
    auth_headers,
    test_application
):

    response = client.post(
        f"/applications/{test_application.id}/resume",
        headers=auth_headers
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Resume file is required"


# ==========================================
# Upload Resume - No File Selected
# ==========================================
def test_upload_resume_no_file_selected(
    client,
    auth_headers,
    test_application
):

    response = client.post(
        f"/applications/{test_application.id}/resume",
        data={
            "resume": (
                BytesIO(b""),
                ""
            )
        },
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "No file selected"


# ==========================================
# Upload Resume - Invalid File Type
# ==========================================
def test_upload_resume_invalid_file_type(
    client,
    auth_headers,
    test_application
):

    fake_file = BytesIO(
        b"this is not a pdf"
    )

    response = client.post(
        f"/applications/{test_application.id}/resume",
        data={
            "resume": (
                fake_file,
                "resume.txt"
            )
        },
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Only PDF files are allowed"


# ==========================================
# Day 6 - Resume Download Tests
# ==========================================

# ==========================================
# Download Resume - No Resume
# ==========================================
def test_download_resume_no_resume(
    client,
    auth_headers,
    test_application
):

    response = client.get(
        f"/applications/{test_application.id}/resume",
        headers=auth_headers
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == (
        "No resume uploaded for this application"
    )


# ==========================================
# Download Resume - File Not Found
# ==========================================
def test_download_resume_file_not_found(
    client,
    auth_headers,
    test_application
):

    test_application.resume_path = (
        "uploads/missing.pdf"
    )

    db.session.commit()

    # Mock filesystem check
    with patch(
        "api.jobs.os.path.exists",
        return_value=False
    ):

        response = client.get(
            f"/applications/{test_application.id}/resume",
            headers=auth_headers
        )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Resume file not found"


# ==========================================
# Download Resume - Success
# ==========================================
def test_download_resume_success(
    client,
    auth_headers,
    test_application
):

    test_application.resume_path = (
        "uploads/test_resume.pdf"
    )

    db.session.commit()

    # Mock filesystem and send_file
    with patch(
        "api.jobs.os.path.exists",
        return_value=True
    ), patch(
        "api.jobs.send_file"
    ) as mock_send_file:

        mock_send_file.return_value = (
            "fake file response"
        )

        response = client.get(
            f"/applications/{test_application.id}/resume",
            headers=auth_headers
        )

    assert response.status_code == 200

    mock_send_file.assert_called_once_with(
        "uploads/test_resume.pdf",
        as_attachment=True
    )


# ==========================================
# Day 6 - Resume Text Extraction Tests
# ==========================================

# ==========================================
# Extract Resume Text - No Resume
# ==========================================
def test_extract_resume_text_no_resume(
    client,
    auth_headers,
    test_application
):

    response = client.get(
        f"/applications/{test_application.id}/resume/text",
        headers=auth_headers
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == (
        "No resume uploaded for this application"
    )


# ==========================================
# Extract Resume Text - File Not Found
# ==========================================
def test_extract_resume_text_file_not_found(
    client,
    auth_headers,
    test_application
):

    test_application.resume_path = (
        "uploads/missing.pdf"
    )

    db.session.commit()

    with patch(
        "api.jobs.os.path.exists",
        return_value=False
    ):

        response = client.get(
            f"/applications/{test_application.id}/resume/text",
            headers=auth_headers
        )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Resume file not found"


# ==========================================
# Extract Resume Text - Success
# ==========================================
def test_extract_resume_text_success(
    client,
    auth_headers,
    test_application
):

    test_application.resume_path = (
        "uploads/test_resume.pdf"
    )

    db.session.commit()

    # Mock PDF page
    mock_page = MagicMock()

    mock_page.extract_text.return_value = (
        "Adithiya\n"
        "Software Developer\n"
        "Python React SQL"
    )

    # Mock PDF reader
    mock_reader = MagicMock()

    mock_reader.pages = [
        mock_page
    ]

    with patch(
        "api.jobs.os.path.exists",
        return_value=True
    ), patch(
        "api.jobs.PdfReader",
        return_value=mock_reader
    ):

        response = client.get(
            f"/applications/{test_application.id}/resume/text",
            headers=auth_headers
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Resume text extracted successfully!"
    )

    assert data["application_id"] == (
        test_application.id
    )

    assert "Adithiya" in data["resume_text"]

    assert "Software Developer" in (
        data["resume_text"]
    )

    assert "Python React SQL" in (
        data["resume_text"]
    )


# ==========================================
# Extract Resume Text - Empty PDF
# ==========================================
def test_extract_resume_text_empty_pdf(
    client,
    auth_headers,
    test_application
):

    test_application.resume_path = (
        "uploads/empty_resume.pdf"
    )

    db.session.commit()

    # Mock page with no extractable text
    mock_page = MagicMock()

    mock_page.extract_text.return_value = ""

    mock_reader = MagicMock()

    mock_reader.pages = [
        mock_page
    ]

    with patch(
        "api.jobs.os.path.exists",
        return_value=True
    ), patch(
        "api.jobs.PdfReader",
        return_value=mock_reader
    ):

        response = client.get(
            f"/applications/{test_application.id}/resume/text",
            headers=auth_headers
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Resume PDF contains no extractable text"
    )

    assert data["application_id"] == (
        test_application.id
    )

    assert data["resume_text"] == ""