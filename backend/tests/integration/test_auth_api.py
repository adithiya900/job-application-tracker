def test_register_and_login_uses_postgres(integration_client):
    register_response = integration_client.post(
        "/register",
        json={
            "name": "Integration Auth User",
            "email": "integration-auth@example.com",
            "password": "password123",
        },
    )

    assert register_response.status_code == 201


    register_data = register_response.get_json()

    assert register_data["message"] == "User registered successfully!"
    assert register_data["email"] == "integration-auth@example.com"
    assert register_data["name"] == "Integration Auth User"

    login_response = integration_client.post(
        "/login",
        json={
            "email": "integration-auth@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.get_json()

    assert login_data["message"] == "Login successful!"
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "integration-auth@example.com"