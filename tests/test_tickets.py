from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models.user import User, UserRole


def registration_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": "secure-password",
        "full_name": email.split("@")[0],
    }


async def register_and_login(client: AsyncClient, email: str) -> str:
    response = await client.post("/auth/register", json=registration_payload(email))
    assert response.status_code == 201

    response = await client.post(
        "/auth/login",
        json={"email": email, "password": "secure-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def set_role(email: str, role: UserRole) -> None:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email))
        assert user is not None
        user.role = role
        session.commit()


def authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_ticket(
    client: AsyncClient, token: str, title: str
) -> dict[str, object]:
    response = await client.post(
        "/tickets",
        headers=authorization_header(token),
        json={"title": title, "description": f"Description for {title}"},
    )
    assert response.status_code == 201
    return response.json()


async def test_user_creates_ticket() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await register_and_login(client, "author@example.com")
        ticket = await create_ticket(client, token, "Cannot sign in")

    assert ticket["title"] == "Cannot sign in"
    assert ticket["status"] == "open"
    assert ticket["assigned_to_id"] is None


async def test_user_sees_only_their_tickets() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first_token = await register_and_login(client, "first@example.com")
        second_token = await register_and_login(client, "second@example.com")
        own_ticket = await create_ticket(client, first_token, "First ticket")
        await create_ticket(client, second_token, "Second ticket")

        response = await client.get(
            "/tickets", headers=authorization_header(first_token)
        )

    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()] == [own_ticket["id"]]


async def test_user_cannot_view_another_users_ticket() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first_token = await register_and_login(client, "first@example.com")
        second_token = await register_and_login(client, "second@example.com")
        ticket = await create_ticket(client, second_token, "Private ticket")

        response = await client.get(
            f"/tickets/{ticket['id']}",
            headers=authorization_header(first_token),
        )

    assert response.status_code == 404


async def test_support_sees_all_tickets() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first_token = await register_and_login(client, "first@example.com")
        second_token = await register_and_login(client, "second@example.com")
        support_token = await register_and_login(client, "support@example.com")
        set_role("support@example.com", UserRole.SUPPORT)
        await create_ticket(client, first_token, "First ticket")
        await create_ticket(client, second_token, "Second ticket")

        response = await client.get(
            "/tickets", headers=authorization_header(support_token)
        )

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_support_changes_ticket_status() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        author_token = await register_and_login(client, "author@example.com")
        support_token = await register_and_login(client, "support@example.com")
        set_role("support@example.com", UserRole.SUPPORT)
        ticket = await create_ticket(client, author_token, "Status update")

        response = await client.patch(
            f"/tickets/{ticket['id']}",
            headers=authorization_header(support_token),
            json={"status": "in_progress"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


async def test_user_cannot_assign_ticket() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        author_token = await register_and_login(client, "author@example.com")
        assignee_token = await register_and_login(client, "assignee@example.com")
        ticket = await create_ticket(client, author_token, "Assignment attempt")
        assignee = await client.get(
            "/users/me", headers=authorization_header(assignee_token)
        )

        response = await client.patch(
            f"/tickets/{ticket['id']}",
            headers=authorization_header(author_token),
            json={"assigned_to_id": assignee.json()["id"]},
        )

    assert response.status_code == 403


async def test_admin_deletes_ticket() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        author_token = await register_and_login(client, "author@example.com")
        admin_token = await register_and_login(client, "admin@example.com")
        set_role("admin@example.com", UserRole.ADMIN)
        ticket = await create_ticket(client, author_token, "Delete me")

        delete_response = await client.delete(
            f"/tickets/{ticket['id']}",
            headers=authorization_header(admin_token),
        )
        get_response = await client.get(
            f"/tickets/{ticket['id']}",
            headers=authorization_header(admin_token),
        )

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


async def test_ticket_limit_and_offset() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await register_and_login(client, "author@example.com")
        for number in range(3):
            await create_ticket(client, token, f"Ticket {number}")

        all_response = await client.get("/tickets", headers=authorization_header(token))
        paged_response = await client.get(
            "/tickets?limit=1&offset=1",
            headers=authorization_header(token),
        )

    assert paged_response.status_code == 200
    assert len(paged_response.json()) == 1
    assert paged_response.json()[0]["id"] == all_response.json()[1]["id"]
