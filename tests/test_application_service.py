import pytest

from app import app
from extensions import db
from models.user import User
from models.job import JobApplication, ApplicationStatus
from services.application_service import ApplicationService
from exceptions.application_exceptions import (
    ApplicationNotFound,
    DuplicateApplication
)


@pytest.fixture(scope="function")
def test_app():

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(test_app):

    user = User(
        name="Test User",
        email="testuser@example.com"
    )

    db.session.add(user)
    db.session.commit()

    return user


def test_create_application(test_app, test_user):

    data = {
        "company": "Google",
        "role": "Software Engineer",
        "status": ApplicationStatus.APPLIED,
        "notes": "Applied through careers page",
        "user_id": test_user.id
    }

    application = ApplicationService.create_application(data)

    assert application.id is not None
    assert application.company == "Google"
    assert application.role == "Software Engineer"
    assert application.status == ApplicationStatus.APPLIED


def test_get_application_by_id(test_app, test_user):

    application = JobApplication(
        company="Microsoft",
        role="Backend Developer",
        status=ApplicationStatus.INTERVIEW,
        notes="Technical interview",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    result = ApplicationService.get_application_by_id(
        application.id
    )

    assert result.company == "Microsoft"
    assert result.role == "Backend Developer"


def test_get_application_not_found(test_app):

    with pytest.raises(ApplicationNotFound):
        ApplicationService.get_application_by_id(99999)


def test_duplicate_application(test_app, test_user):

    data = {
        "company": "Amazon",
        "role": "Python Developer",
        "status": ApplicationStatus.APPLIED,
        "notes": "First application",
        "user_id": test_user.id
    }

    ApplicationService.create_application(data)

    with pytest.raises(DuplicateApplication):
        ApplicationService.create_application(data)


def test_update_application(test_app, test_user):

    application = JobApplication(
        company="Meta",
        role="Frontend Developer",
        status=ApplicationStatus.APPLIED,
        notes="Initial application",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    updated_data = {
        "status": ApplicationStatus.INTERVIEW,
        "notes": "Interview scheduled"
    }

    updated_application = ApplicationService.update_application(
        application.id,
        updated_data
    )

    assert updated_application.status == ApplicationStatus.INTERVIEW
    assert updated_application.notes == "Interview scheduled"


def test_delete_application(test_app, test_user):

    application = JobApplication(
        company="Netflix",
        role="Software Developer",
        status=ApplicationStatus.APPLIED,
        notes="Testing delete",
        user_id=test_user.id
    )

    db.session.add(application)
    db.session.commit()

    ApplicationService.delete_application(application.id)

    deleted_application = db.session.get(
        JobApplication,
        application.id
    )

    assert deleted_application is None


def test_delete_application_not_found(test_app):

    with pytest.raises(ApplicationNotFound):
        ApplicationService.delete_application(99999)