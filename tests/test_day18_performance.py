"""
Day 18 -- API & Web -- Performance Optimisation
Tests for:
  - Analytics endpoint correctness
  - Redis/SimpleCache caching (MISS -> SET -> HIT)
  - Cache invalidation on mutations
  - User-specific cache isolation
  - Empty analytics edge case
"""
import pytest
from extensions import db, bcrypt, cache
from models.user import User
from models.job import JobApplication, ApplicationStatus
from flask_jwt_extended import create_access_token
from datetime import date, timedelta
import json


# -----------------------------------------------
# Fixtures
# -----------------------------------------------

@pytest.fixture
def perf_user(test_app):
    """Create a fresh user for Day-18 performance tests."""
    with test_app.app_context():
        hashed = bcrypt.generate_password_hash("password123").decode("utf-8")
        user = User(name="Perf User", email="perf18@example.com", password=hashed)
        db.session.add(user)
        db.session.commit()
        uid = user.id
    return uid


@pytest.fixture
def perf_applications(test_app, perf_user):
    """Create two applications for the perf_user."""
    with test_app.app_context():
        app1 = JobApplication(
            company="Company A",
            role="Dev",
            status=ApplicationStatus.APPLIED,
            user_id=perf_user,
            applied_date=date.today() - timedelta(days=2),
        )
        app2 = JobApplication(
            company="Company B",
            role="Dev",
            status=ApplicationStatus.INTERVIEW,
            user_id=perf_user,
            applied_date=date.today() - timedelta(days=1),
        )
        db.session.add_all([app1, app2])
        db.session.commit()
        return [app1.id, app2.id]


@pytest.fixture
def perf_token(test_app, perf_user):
    """JWT token for perf_user."""
    with test_app.app_context():
        return create_access_token(identity=str(perf_user))


@pytest.fixture
def perf_headers(perf_token):
    return {"Authorization": f"Bearer {perf_token}"}


# -----------------------------------------------
# 1. Authenticated analytics returns 200
# -----------------------------------------------

def test_analytics_returns_200(client, perf_user, perf_applications, perf_headers, test_app):
    """GET /api/analytics with valid JWT -> 200."""
    with test_app.app_context():
        cache.clear()
    response = client.get("/api/analytics", headers=perf_headers)
    assert response.status_code == 200


# -----------------------------------------------
# 2. Analytics contains all five required metrics
# -----------------------------------------------

def test_analytics_contains_all_five_metrics(client, perf_user, perf_applications, perf_headers, test_app):
    """Response must contain total_applications, response_rate, time_in_stage,
    best_day_of_week, by_status."""
    with test_app.app_context():
        cache.clear()
    response = client.get("/api/analytics", headers=perf_headers)
    data = response.get_json()

    assert "total_applications" in data
    assert "response_rate" in data
    assert "time_in_stage" in data
    assert "best_day_of_week" in data
    assert "by_status" in data


# -----------------------------------------------
# 3. Correctness: total_applications, response_rate, by_status
# -----------------------------------------------

def test_analytics_correctness(client, perf_user, perf_applications, perf_headers, test_app):
    """Two apps: one APPLIED, one INTERVIEW -> total=2, response_rate=50.0."""
    with test_app.app_context():
        cache.clear()
    response = client.get("/api/analytics", headers=perf_headers)
    assert response.status_code == 200
    data = response.get_json()

    assert data["total_applications"] == 2
    assert data["response_rate"] == 50.0

    # All ApplicationStatus values must be in by_status
    for s in ApplicationStatus:
        assert s.value in data["by_status"]

    assert data["by_status"]["APPLIED"] == 1
    assert data["by_status"]["INTERVIEW"] == 1
    assert data["by_status"]["OFFER"] == 0
    assert data["by_status"]["REJECTED"] == 0


# -----------------------------------------------
# 4. Cache MISS stores result in cache
# -----------------------------------------------

def test_cache_miss_stores_result(client, test_app, perf_user, perf_applications, perf_headers):
    """After first request (cache MISS), result must be stored in cache."""
    with test_app.app_context():
        cache.clear()
        assert cache.get(f"analytics:user:{perf_user}") is None

    response = client.get("/api/analytics", headers=perf_headers)
    assert response.status_code == 200

    with test_app.app_context():
        cached = cache.get(f"analytics:user:{perf_user}")
        assert cached is not None, "Cache should be populated after first request"
        assert cached["total_applications"] == 2


# -----------------------------------------------
# 5. Cache HIT returns cached result
# -----------------------------------------------

def test_cache_hit_returns_cached_result(client, test_app, perf_user, perf_applications, perf_headers):
    """Second request (cache HIT) returns same data as first request."""
    with test_app.app_context():
        cache.clear()

    response1 = client.get("/api/analytics", headers=perf_headers)
    assert response1.status_code == 200
    data1 = response1.get_json()

    response2 = client.get("/api/analytics", headers=perf_headers)
    assert response2.status_code == 200
    data2 = response2.get_json()

    assert data1 == data2, "Cache HIT must return identical result to MISS"


# -----------------------------------------------
# 6. Cache is user-specific (isolation)
# -----------------------------------------------

def test_cache_is_user_specific(client, test_app, perf_user, perf_applications, perf_headers):
    """Two different users must have independent cache entries."""
    with test_app.app_context():
        cache.clear()
        hashed = bcrypt.generate_password_hash("pass").decode("utf-8")
        user2 = User(name="Other User", email="other18@example.com", password=hashed)
        db.session.add(user2)
        db.session.commit()
        user2_id = user2.id

    token2 = create_access_token(identity=str(user2_id))
    headers2 = {"Authorization": f"Bearer {token2}"}

    response1 = client.get("/api/analytics", headers=perf_headers)
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1["total_applications"] == 2

    response2 = client.get("/api/analytics", headers=headers2)
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2["total_applications"] == 0

    with test_app.app_context():
        cached1 = cache.get(f"analytics:user:{perf_user}")
        cached2 = cache.get(f"analytics:user:{user2_id}")
        assert cached1 is not None
        assert cached2 is not None
        assert cached1["total_applications"] == 2
        assert cached2["total_applications"] == 0


# -----------------------------------------------
# 7. Cache invalidation on create
# -----------------------------------------------

def test_cache_invalidation_on_create(client, test_app, perf_user, perf_applications, perf_headers):
    """Creating an application must invalidate the analytics cache."""
    with test_app.app_context():
        cache.clear()

    response1 = client.get("/api/analytics", headers=perf_headers)
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1["total_applications"] == 2

    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is not None

    new_app = {"company": "Company C", "role": "Dev", "status": "APPLIED"}
    create_resp = client.post("/api/applications", json=new_app, headers=perf_headers)
    assert create_resp.status_code == 201

    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is None, \
            "Cache must be invalidated after creating an application"

    response2 = client.get("/api/analytics", headers=perf_headers)
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2["total_applications"] == 3


# -----------------------------------------------
# 8. Cache invalidation on update
# -----------------------------------------------

def test_cache_invalidation_on_update(client, test_app, perf_user, perf_applications, perf_headers):
    """Updating an application status must invalidate the analytics cache."""
    with test_app.app_context():
        cache.clear()

    client.get("/api/analytics", headers=perf_headers)
    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is not None

    app_id = perf_applications[0]
    update_resp = client.put(
        f"/api/applications/{app_id}",
        json={"status": "OFFER"},
        headers=perf_headers
    )
    assert update_resp.status_code == 200

    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is None


# -----------------------------------------------
# 9. Cache invalidation on delete
# -----------------------------------------------

def test_cache_invalidation_on_delete(client, test_app, perf_user, perf_applications, perf_headers):
    """Deleting an application must invalidate the analytics cache."""
    with test_app.app_context():
        cache.clear()

    client.get("/api/analytics", headers=perf_headers)
    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is not None

    app_id = perf_applications[0]
    del_resp = client.delete(f"/api/applications/{app_id}", headers=perf_headers)
    assert del_resp.status_code == 200

    with test_app.app_context():
        assert cache.get(f"analytics:user:{perf_user}") is None


# -----------------------------------------------
# 10. Empty analytics works correctly
# -----------------------------------------------

def test_empty_analytics(client, test_app):
    """User with zero applications: safe zero values, no crash."""
    with test_app.app_context():
        cache.clear()
        hashed = bcrypt.generate_password_hash("pass").decode("utf-8")
        user = User(name="Empty User", email="empty18@example.com", password=hashed)
        db.session.add(user)
        db.session.commit()
        uid = user.id

    token = create_access_token(identity=str(uid))
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/analytics", headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert data["total_applications"] == 0
    assert data["response_rate"] == 0
    assert data["best_day_of_week"]["day"] is None
    assert data["best_day_of_week"]["success_rate"] == 0
    for s in ApplicationStatus:
        assert data["by_status"][s.value] == 0


# -----------------------------------------------
# 11. Unauthenticated request returns 401
# -----------------------------------------------

def test_analytics_requires_auth(client, test_app):
    """GET /api/analytics without JWT -> 401."""
    response = client.get("/api/analytics")
    assert response.status_code == 401


# -----------------------------------------------
# 12. Cache MISS JSON == Cache HIT JSON
# -----------------------------------------------

def test_cache_miss_equals_cache_hit(client, test_app, perf_user, perf_applications, perf_headers):
    """cache MISS response JSON must equal cache HIT response JSON."""
    with test_app.app_context():
        cache.clear()

    miss_response = client.get("/api/analytics", headers=perf_headers)
    assert miss_response.status_code == 200
    miss_data = miss_response.get_json()

    hit_response = client.get("/api/analytics", headers=perf_headers)
    assert hit_response.status_code == 200
    hit_data = hit_response.get_json()

    assert miss_data == hit_data, "Cache MISS JSON must equal cache HIT JSON"


# -----------------------------------------------
# 13. by_status contains all ApplicationStatus values
# -----------------------------------------------

def test_by_status_has_all_values(client, test_app, perf_user, perf_applications, perf_headers):
    """by_status must include every ApplicationStatus enum value."""
    with test_app.app_context():
        cache.clear()
    response = client.get("/api/analytics", headers=perf_headers)
    data = response.get_json()

    expected = {s.value for s in ApplicationStatus}
    actual = set(data["by_status"].keys())
    assert expected == actual, f"by_status keys mismatch: expected {expected}, got {actual}"


# -----------------------------------------------
# 14. get_analytics service method exists
# -----------------------------------------------

def test_get_analytics_method_exists():
    """ApplicationService.get_analytics must exist."""
    from services.application_service import ApplicationService
    assert callable(getattr(ApplicationService, "get_analytics"))


# -----------------------------------------------
# 15. Index existence
# -----------------------------------------------

def test_indexes_exist(test_app):
    from sqlalchemy import inspect
    with test_app.app_context():
        inspector = inspect(db.engine)
        indexes = inspector.get_indexes('job_applications')
        index_names = [idx['name'] for idx in indexes]
        assert 'ix_job_applications_user_id' in index_names
        assert 'ix_job_applications_status' in index_names
        assert 'ix_job_applications_applied_date' in index_names


# -----------------------------------------------
# 16. N+1 / query-count regression
# -----------------------------------------------

def test_no_n_plus_one_queries(client, test_app, perf_user, perf_applications, perf_headers):
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    with test_app.app_context():
        cache.clear()

    query_count = [0]
    
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_count[0] += 1
        
    event.listen(Engine, "before_cursor_execute", before_cursor_execute)
    
    try:
        response = client.get("/api/analytics", headers=perf_headers)
        assert response.status_code == 200
        # The number of queries should be small and constant (e.g., < 10)
        assert query_count[0] < 10, f"Query count too high: {query_count[0]}"
    finally:
        event.remove(Engine, "before_cursor_execute", before_cursor_execute)


# -----------------------------------------------
# 17. Redis cache backend and 300-second TTL
# -----------------------------------------------

def test_redis_cache_and_ttl(client, test_app, perf_user, perf_headers):
    with test_app.app_context():
        # Only run this test if Redis is the backend
        if test_app.config["CACHE_TYPE"] != "RedisCache":
            pytest.skip("Not using RedisCache")
            
        cache.clear()
        
    # MISS
    response = client.get("/api/analytics", headers=perf_headers)
    assert response.status_code == 200
    
    with test_app.app_context():
        # Get actual redis client from flask-caching
        # Flask-Caching's RedisCache stores the redis client in cache._client
        # The default key prefix is flask_cache_ unless configured otherwise
        redis_client = getattr(cache.cache, "_read_client", getattr(cache.cache, "_client", None))
        if redis_client:
            # Check key exists and has TTL
            # Flask-Caching uses CACHE_KEY_PREFIX, default is often empty or depends on config
            prefix = cache.cache.key_prefix or ""
            key = f"{prefix}analytics:user:{perf_user}"
            ttl = redis_client.ttl(key)
            # The TTL should be 300 seconds. Depending on exact timing, it might be 299 or 300.
            assert ttl > 0, "TTL must be set"
            assert ttl <= 300, f"TTL too high: {ttl}"
            assert ttl > 290, f"TTL too low: {ttl}"

