from httpx import ASGITransport, AsyncClient

from app.main import app


def user_payload() -> dict[str, str]:
    return {
        "email": "user@example.com",
        "password": "secure-password",
        "full_name": "Test User",
    }


async def register_user(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json=user_payload())
    assert response.status_code == 201


async def test_register_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/register", json=user_payload())

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["role"] == "user"
    assert "hashed_password" not in response.json()


async def test_register_user_with_existing_email_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await register_user(client)
        response = await client.post("/auth/register", json=user_payload())

    assert response.status_code == 409


async def test_login_and_get_current_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await register_user(client)
        login_response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "secure-password"},
        )

        token = login_response.json()["access_token"]
        me_response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert login_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"


async def test_login_with_wrong_password_is_rejected() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await register_user(client)
        response = await client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )

    assert response.status_code == 401
