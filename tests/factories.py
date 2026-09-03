import factory

from models.user import User
from models.job import JobApplication, ApplicationStatus


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    name = factory.Faker("name")
    email = factory.Sequence(
        lambda n: f"testuser{n}@example.com"
    )
    password = "testpassword123"


class ApplicationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = JobApplication
        sqlalchemy_session_persistence = "flush"

    company = factory.Faker("company")
    role = factory.Faker("job")
    status = ApplicationStatus.APPLIED
    notes = factory.Faker("sentence")
    user = factory.SubFactory(UserFactory)