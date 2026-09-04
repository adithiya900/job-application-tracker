import pytest

from app import app
from extensions import db
from tests.factories import UserFactory, ApplicationFactory


@pytest.fixture(scope="function")
def test_app():

    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Use in-memory cache in tests — does not require Redis
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 1800

    # Re-initialize cache with SimpleCache to avoid Redis in tests
    from extensions import cache
    cache.init_app(app)

    with app.app_context():

        db.drop_all()
        db.create_all()

        # Connect Factory Boy to the current SQLAlchemy session
        UserFactory._meta.sqlalchemy_session = db.session
        ApplicationFactory._meta.sqlalchemy_session = db.session

        yield app

        db.session.remove()
        db.drop_all()




@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def test_user(test_app):
    return UserFactory()


@pytest.fixture
def test_application(test_app, test_user):
    return ApplicationFactory(user=test_user)


@pytest.fixture
def auth_headers(test_app, test_user):

    from flask_jwt_extended import create_access_token

    access_token = create_access_token(
        identity=str(test_user.id)
    )

    return {
        "Authorization": f"Bearer {access_token}"
    }
