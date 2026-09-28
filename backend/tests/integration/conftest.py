from testcontainers.community.redis import RedisContainer
from sqlalchemy import create_engine
from app import app
from extensions import db
from extensions import cache
import pytest
from testcontainers.community.postgres import PostgresContainer



@pytest.fixture(scope="session")
def postgres_container():
    container = PostgresContainer("postgres:16-alpine")
    container.start()

    try:
        yield container
    finally:
        container.stop()

@pytest.fixture(scope="session")
def redis_container():
    container = RedisContainer("redis:7-alpine")
    container.start()

    try:
        yield container
    finally:
        container.stop()

@pytest.fixture(scope="session")
def redis_client(redis_container):
    return redis_container.get_client()        

@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    return postgres_container.get_connection_url()

@pytest.fixture(scope="session")
def postgres_engine(postgres_url):
    engine = create_engine(postgres_url)

    try:
        yield engine
    finally:
        engine.dispose()

@pytest.fixture(scope="session")
def postgres_schema(postgres_engine):
    with app.app_context():
        db.metadata.create_all(postgres_engine)

    yield

    db.metadata.drop_all(postgres_engine)

@pytest.fixture
def clean_postgres_db(postgres_schema, postgres_engine):
    db.metadata.drop_all(postgres_engine)
    db.metadata.create_all(postgres_engine)

    yield    

@pytest.fixture
def integration_client(postgres_schema, postgres_engine, redis_container, redis_client):
    original_engines = db._app_engines[app]
    original_read_client = cache.cache._read_client
    original_write_client = cache.cache._write_client

    app.config["TESTING"] = True
    db._app_engines[app] = {None: postgres_engine}

    cache.cache._read_client = redis_client
    cache.cache._write_client = redis_client

    try:
        with app.app_context():
            with app.test_client() as client:
                yield client

            db.session.remove()
    finally:
        db._app_engines[app] = original_engines
        cache.cache._read_client = original_read_client
        cache.cache._write_client = original_write_client