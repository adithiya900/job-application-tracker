def test_health_check_uses_integration_services(integration_client):
    response = integration_client.get("/api/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"