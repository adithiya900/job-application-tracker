import pytest
from unittest.mock import patch

from extensions import db
from models.job import JobApplication, ApplicationStatus
from services.application_service import ApplicationService
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)


# ==========================================
# Create Application
# ==========================================
def test_create_application(
    test_app,
    test_user
):

    data = {
        "company": "Google",
        "role": "Software Engineer",
        "status": ApplicationStatus.APPLIED,
        "notes": "Applied through careers page"
    }

    application = ApplicationService.create_application(
        data,
        test_user.id
    )

    assert application.id is not None
    assert application.company == "Google"
    assert application.role == "Software Engineer"
    assert application.status == ApplicationStatus.APPLIED
    assert application.user_id == test_user.id


# ==========================================
# Create Application - Default Status
# ==========================================
def test_create_application_default_status(
    test_app,
    test_user
):

    data = {
        "company": "Microsoft",
        "role": "Backend Developer",
        "notes": "Testing default status"
    }

    application = ApplicationService.create_application(
        data,
        test_user.id
    )

    assert application.status == ApplicationStatus.APPLIED


# ==========================================
# Create Application - Duplicate
# ==========================================
def test_duplicate_application(
    test_app,
    test_user
):

    data = {
        "company": "Amazon",
        "role": "Python Developer",
        "status": ApplicationStatus.APPLIED,
        "notes": "First application"
    }

    ApplicationService.create_application(
        data,
        test_user.id
    )

    with pytest.raises(DuplicateApplication):

        ApplicationService.create_application(
            data,
            test_user.id
        )


# ==========================================
# Get All Applications
# ==========================================
def test_get_all_applications(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Software Engineer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.INTERVIEW
        },
        test_user.id
    )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id
    )

    assert result.total == 2
    assert result.page == 1
    assert result.per_page == 5


# ==========================================
# Get All Applications - Search
# ==========================================
def test_get_all_applications_search(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Software Engineer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.INTERVIEW
        },
        test_user.id
    )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        search="Google"
    )

    assert result.total == 1
    assert result.items[0].company == "Google"


# ==========================================
# Get All Applications - Search Role
# ==========================================
def test_get_all_applications_search_role(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Frontend Developer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.INTERVIEW
        },
        test_user.id
    )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        search="Backend"
    )

    assert result.total == 1
    assert result.items[0].role == "Backend Developer"


# ==========================================
# Get All Applications - Status Filter
# ==========================================
def test_get_all_applications_status_filter(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Software Engineer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.INTERVIEW
        },
        test_user.id
    )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        status=ApplicationStatus.INTERVIEW
    )

    assert result.total == 1
    assert result.items[0].status == ApplicationStatus.INTERVIEW


# ==========================================
# Get All Applications - Oldest Sort
# ==========================================
def test_get_all_applications_oldest_sort(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Software Engineer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    applications = JobApplication.query.filter_by(
        user_id=test_user.id
    ).order_by(
        JobApplication.id.asc()
    ).all()

    applications[0].applied_date = (
        applications[0].applied_date
    )

    db.session.commit()

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        sort="oldest"
    )

    assert result.total == 2


# ==========================================
# Get All Applications - Company Sort
# ==========================================
def test_get_all_applications_company_sort(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Zomato",
            "role": "Developer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Developer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        sort="company"
    )

    assert result.total == 2
    assert result.items[0].company == "Amazon"


# ==========================================
# Get All Applications - Pagination
# ==========================================
def test_get_all_applications_pagination(
    test_app,
    test_user
):

    for number in range(7):

        ApplicationService.create_application(
            {
                "company": f"Company {number}",
                "role": "Software Developer",
                "status": ApplicationStatus.APPLIED
            },
            test_user.id
        )

    result = ApplicationService.get_all_applications(
        user_id=test_user.id,
        page=2,
        per_page=5
    )

    assert result.total == 7
    assert result.page == 2
    assert result.per_page == 5
    assert len(result.items) == 2


# ==========================================
# Get Application By ID
# ==========================================
def test_get_application_by_id(
    test_app,
    test_user,
    test_application
):

    result = ApplicationService.get_application_by_id(
        test_application.id,
        test_user.id
    )

    assert result.company == test_application.company
    assert result.role == test_application.role
    assert result.user_id == test_user.id


# ==========================================
# Get Application By ID - Not Found
# ==========================================
def test_get_application_not_found(
    test_app,
    test_user
):

    with pytest.raises(ApplicationNotFound):

        ApplicationService.get_application_by_id(
            99999,
            test_user.id
        )


# ==========================================
# Update Application
# ==========================================
def test_update_application(
    test_app,
    test_user,
    test_application
):

    updated_data = {
        "status": ApplicationStatus.INTERVIEW,
        "notes": "Interview scheduled"
    }

    updated_application = (
        ApplicationService.update_application(
            test_application.id,
            updated_data,
            test_user.id
        )
    )

    assert updated_application.status == (
        ApplicationStatus.INTERVIEW
    )

    assert updated_application.notes == (
        "Interview scheduled"
    )

    assert updated_application.user_id == (
        test_user.id
    )


# ==========================================
# Update Application - Company and Role
# ==========================================
def test_update_application_company_role(
    test_app,
    test_user,
    test_application
):

    updated_data = {
        "company": "Microsoft",
        "role": "Senior Software Engineer"
    }

    updated_application = (
        ApplicationService.update_application(
            test_application.id,
            updated_data,
            test_user.id
        )
    )

    assert updated_application.company == "Microsoft"

    assert updated_application.role == (
        "Senior Software Engineer"
    )


# ==========================================
# Update Application - Not Found
# ==========================================
def test_update_application_not_found(
    test_app,
    test_user
):

    with pytest.raises(ApplicationNotFound):

        ApplicationService.update_application(
            99999,
            {
                "notes": "Updated"
            },
            test_user.id
        )


# ==========================================
# Delete Application
# ==========================================
def test_delete_application(
    test_app,
    test_user,
    test_application
):

    application_id = test_application.id

    ApplicationService.delete_application(
        application_id,
        test_user.id
    )

    deleted_application = db.session.get(
        JobApplication,
        application_id
    )

    assert deleted_application is None


# ==========================================
# Delete Application - Resume File
# ==========================================
def test_delete_application_with_resume(
    test_app,
    test_user,
    test_application
):

    test_application.resume_path = (
        "uploads/test_resume.pdf"
    )

    db.session.commit()

    with patch(
        "services.application_service.os.path.exists",
        return_value=True
    ) as mock_exists, patch(
        "services.application_service.os.remove"
    ) as mock_remove:

        ApplicationService.delete_application(
            test_application.id,
            test_user.id
        )

    mock_exists.assert_called_once_with(
        "uploads/test_resume.pdf"
    )

    mock_remove.assert_called_once_with(
        "uploads/test_resume.pdf"
    )

    deleted_application = db.session.get(
        JobApplication,
        test_application.id
    )

    assert deleted_application is None


# ==========================================
# Delete Application - Resume File Missing
# ==========================================
def test_delete_application_resume_file_not_found(
    test_app,
    test_user,
    test_application
):

    test_application.resume_path = (
        "uploads/missing_resume.pdf"
    )

    db.session.commit()

    with patch(
        "services.application_service.os.path.exists",
        return_value=False
    ) as mock_exists, patch(
        "services.application_service.os.remove"
    ) as mock_remove:

        ApplicationService.delete_application(
            test_application.id,
            test_user.id
        )

    mock_exists.assert_called_once_with(
        "uploads/missing_resume.pdf"
    )

    mock_remove.assert_not_called()

    deleted_application = db.session.get(
        JobApplication,
        test_application.id
    )

    assert deleted_application is None


# ==========================================
# Delete Application - Not Found
# ==========================================
def test_delete_application_not_found(
    test_app,
    test_user
):

    with pytest.raises(ApplicationNotFound):

        ApplicationService.delete_application(
            99999,
            test_user.id
        )


# ==========================================
# Dashboard Statistics
# ==========================================
def test_get_dashboard_statistics(
    test_app,
    test_user
):

    ApplicationService.create_application(
        {
            "company": "Google",
            "role": "Developer",
            "status": ApplicationStatus.APPLIED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Amazon",
            "role": "Backend Developer",
            "status": ApplicationStatus.INTERVIEW
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Microsoft",
            "role": "Software Engineer",
            "status": ApplicationStatus.REJECTED
        },
        test_user.id
    )

    ApplicationService.create_application(
        {
            "company": "Meta",
            "role": "Frontend Developer",
            "status": ApplicationStatus.OFFER
        },
        test_user.id
    )

    statistics = (
        ApplicationService.get_dashboard_statistics(
            test_user.id
        )
    )

    assert statistics["total_applications"] == 4
    assert statistics["applied"] == 1
    assert statistics["interview"] == 1
    assert statistics["rejected"] == 1
    assert statistics["offered"] == 1


# ==========================================
# Dashboard Statistics - Empty
# ==========================================
def test_get_dashboard_statistics_empty(
    test_app,
    test_user
):

    statistics = (
        ApplicationService.get_dashboard_statistics(
            test_user.id
        )
    )

    assert statistics["total_applications"] == 0
    assert statistics["applied"] == 0
    assert statistics["interview"] == 0
    assert statistics["rejected"] == 0
    assert statistics["offered"] == 0