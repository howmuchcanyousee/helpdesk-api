from collections.abc import Callable

from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from tests.conftest import AuthenticatedClient


def ticket_payload(title: str = "Cannot sign in") -> dict[str, str]:
    return {
        "title": title,
        "description": f"Description for {title}",
    }


async def create_ticket(
    client: AuthenticatedClient,
    title: str = "Cannot sign in",
) -> dict[str, object]:
    response = await client.client.post(
        "/tickets",
        headers=client.headers,
        json=ticket_payload(title),
    )
    assert response.status_code == 201
    return response.json()


async def test_user_creates_reads_and_edits_ticket(
    user_client: AuthenticatedClient,
) -> None:
    ticket = await create_ticket(user_client)
    get_response = await user_client.client.get(
        f"/tickets/{ticket['id']}",
        headers=user_client.headers,
    )
    update_response = await user_client.client.patch(
        f"/tickets/{ticket['id']}",
        headers=user_client.headers,
        json={"title": "Updated title"},
    )

    assert ticket["status"] == "open"
    assert ticket["assigned_to_id"] is None
    assert get_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated title"
    assert update_response.json()["description"] == ticket["description"]


async def test_user_sees_only_own_tickets_and_cannot_view_foreign_ticket(
    user_client: AuthenticatedClient,
    user_factory: Callable[[str, UserRole], User],
    ticket_factory: Callable[..., Ticket],
) -> None:
    other_user = user_factory("other@example.com", UserRole.USER)
    own_ticket = ticket_factory(user_client.user, title="Own ticket")
    foreign_ticket = ticket_factory(other_user, title="Foreign ticket")

    list_response = await user_client.client.get(
        "/tickets", headers=user_client.headers
    )
    get_response = await user_client.client.get(
        f"/tickets/{foreign_ticket.id}",
        headers=user_client.headers,
    )

    assert [ticket["id"] for ticket in list_response.json()] == [own_ticket.id]
    assert get_response.status_code == 404


async def test_support_sees_all_tickets_and_updates_assignment_and_status(
    support_client: AuthenticatedClient,
    user: User,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user)

    list_response = await support_client.client.get(
        "/tickets",
        headers=support_client.headers,
    )
    update_response = await support_client.client.patch(
        f"/tickets/{ticket.id}",
        headers=support_client.headers,
        json={"status": "in_progress", "assigned_to_id": support_client.user.id},
    )

    assert len(list_response.json()) == 1
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "in_progress"
    assert update_response.json()["assigned_to_id"] == support_client.user.id


async def test_user_cannot_change_status_or_assign_ticket(
    user_client: AuthenticatedClient,
    support_user: User,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    response = await user_client.client.patch(
        f"/tickets/{ticket.id}",
        headers=user_client.headers,
        json={"status": "resolved", "assigned_to_id": support_user.id},
    )

    assert response.status_code == 403


async def test_admin_deletes_ticket(
    admin_client: AuthenticatedClient,
    user: User,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user)
    delete_response = await admin_client.client.delete(
        f"/tickets/{ticket.id}",
        headers=admin_client.headers,
    )
    get_response = await admin_client.client.get(
        f"/tickets/{ticket.id}",
        headers=admin_client.headers,
    )

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


async def test_ticket_filters(
    support_client: AuthenticatedClient,
    user: User,
    ticket_factory: Callable[..., Ticket],
) -> None:
    matching_ticket = ticket_factory(
        user,
        status=TicketStatus.OPEN,
        priority=TicketPriority.HIGH,
        assigned_to=support_client.user,
    )
    ticket_factory(user, status=TicketStatus.RESOLVED, priority=TicketPriority.LOW)

    response = await support_client.client.get(
        (
            "/tickets?status=open&priority=high"
            f"&author_id={user.id}&assigned_to_id={support_client.user.id}"
        ),
        headers=support_client.headers,
    )

    assert response.status_code == 200
    assert [ticket["id"] for ticket in response.json()] == [matching_ticket.id]


async def test_ticket_limit_and_offset(
    user_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    for number in range(3):
        ticket_factory(user_client.user, title=f"Ticket {number}")

    all_response = await user_client.client.get("/tickets", headers=user_client.headers)
    paged_response = await user_client.client.get(
        "/tickets?limit=1&offset=1",
        headers=user_client.headers,
    )

    assert len(paged_response.json()) == 1
    assert paged_response.json()[0]["id"] == all_response.json()[1]["id"]


async def test_ticket_requires_title_and_description(
    user_client: AuthenticatedClient,
) -> None:
    response = await user_client.client.post(
        "/tickets",
        headers=user_client.headers,
        json={"title": "Incomplete ticket"},
    )

    assert response.status_code == 422
