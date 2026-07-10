from httpx import AsyncClient


def registration_payload() -> dict[str, str]:
    return {
        "email": "new-user@example.com",
        "password": "secure-password",
        "full_name": "New User",
    }


async def test_register_user(api_client: AsyncClient) -> None:
    response = await api_client.post("/auth/register", json=registration_payload())

    assert response.status_code == 201
    assert response.json()["email"] == "new-user@example.com"
    assert response.json()["role"] == "user"
    assert "hashed_password" not in response.json()


async def test_register_user_with_existing_email_is_rejected(
    api_client: AsyncClient,
) -> None:
    await api_client.post("/auth/register", json=registration_payload())
    response = await api_client.post("/auth/register", json=registration_payload())

    assert response.status_code == 409


async def test_login_and_get_current_user(api_client: AsyncClient) -> None:
    await api_client.post("/auth/register", json=registration_payload())
    login_response = await api_client.post(
        "/auth/login",
        json={"email": "new-user@example.com", "password": "secure-password"},
    )

    token = login_response.json()["access_token"]
    me_response = await api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "new-user@example.com"


async def test_login_with_wrong_password_is_rejected(api_client: AsyncClient) -> None:
    await api_client.post("/auth/register", json=registration_payload())
    response = await api_client.post(
        "/auth/login",
        json={"email": "new-user@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


async def test_register_and_login_validate_required_fields(
    api_client: AsyncClient,
) -> None:
    register_response = await api_client.post(
        "/auth/register",
        json={"email": "new-user@example.com"},
    )
    login_response = await api_client.post("/auth/login", json={})

    assert register_response.status_code == 422
    assert login_response.status_code == 422
