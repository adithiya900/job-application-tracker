from flask_jwt_extended import create_access_token

from extensions import cache
from tests.factories import UserFactory


def test_analytics_cache_uses_redis_and_300_second_ttl(
    integration_client,
    clean_postgres_db,
    redis_client,
):
    with integration_client.application.app_context():
        cache.clear()

        user = UserFactory()
        user_id = user.id
        token = create_access_token(identity=str(user_id))

    response = integration_client.get(
        "/api/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    with integration_client.application.app_context():
        # Flask-Caching prepends its key prefix to every Redis key, so the raw
        # "analytics:user:<id>" name is not what is actually stored.
        prefix = cache.cache.key_prefix or ""
        key = f"{prefix}analytics:user:{user_id}"
        ttl = redis_client.ttl(key)

    assert ttl > 0, f"Expected Redis cache key {key!r} to exist"
    assert ttl <= 300, f"Expected TTL <= 300 seconds, got {ttl}"
    assert ttl > 290, f"Expected TTL > 290 seconds, got {ttl}"
