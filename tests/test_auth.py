from datetime import UTC, datetime, timedelta

import jwt
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from tests.conftest import AuthenticatedClient


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

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == "new-user@example.com"))
        assert user is not None
        assert user.hashed_password != "secure-password"
        assert user.hashed_password.startswith("$2")


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


async def test_users_me_requires_valid_token(api_client: AsyncClient) -> None:
    missing_response = await api_client.get("/users/me")
    invalid_response = await api_client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    expired_token = jwt.encode(
        {"sub": "user@example.com", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    expired_response = await api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    token_without_expiry = jwt.encode(
        {"sub": "user@example.com"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    missing_claim_response = await api_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token_without_expiry}"},
    )

    assert missing_response.status_code == 401
    assert invalid_response.status_code == 401
    assert expired_response.status_code == 401
    assert missing_claim_response.status_code == 401


async def test_inactive_user_cannot_access_api(
    user_client: AuthenticatedClient,
) -> None:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.id == user_client.user.id))
        assert user is not None
        user.is_active = False
        session.commit()

    response = await user_client.client.get("/users/me", headers=user_client.headers)
    login_response = await user_client.client.post(
        "/auth/login",
        json={"email": user_client.user.email, "password": "secure-password"},
    )

    assert response.status_code == 403
    assert login_response.status_code == 401


async def test_register_rejects_mass_assignment_and_unsafe_passwords(
    api_client: AsyncClient,
) -> None:
    payload = registration_payload()
    payload["role"] = "admin"
    mass_assignment_response = await api_client.post("/auth/register", json=payload)

    unicode_payload = registration_payload()
    unicode_payload["email"] = "unicode@example.com"
    unicode_payload["password"] = "я" * 40
    unicode_response = await api_client.post("/auth/register", json=unicode_payload)

    nul_payload = registration_payload()
    nul_payload["email"] = "nul@example.com"
    nul_payload["password"] = "password\x00value"
    nul_response = await api_client.post("/auth/register", json=nul_payload)

    assert mass_assignment_response.status_code == 422
    assert unicode_response.status_code == 422
    assert nul_response.status_code == 422


def test_swagger_uses_http_bearer_authentication() -> None:
    from app.main import app

    security_schemes = app.openapi()["components"]["securitySchemes"]

    assert security_schemes == {"HTTPBearer": {"type": "http", "scheme": "bearer"}}
