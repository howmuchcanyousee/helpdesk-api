from collections.abc import Callable

from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from tests.conftest import AuthenticatedClient


async def create_comment(
    client: AuthenticatedClient,
    ticket_id: int,
    text: str = "Test comment",
) -> dict[str, object]:
    response = await client.client.post(
        f"/tickets/{ticket_id}/comments",
        headers=client.headers,
        json={"text": text},
    )
    assert response.status_code == 201
    return response.json()


async def test_user_creates_and_lists_comments_on_own_ticket(
    user_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    first_comment = await create_comment(user_client, ticket.id, "First comment")
    await create_comment(user_client, ticket.id, "Second comment")
    list_response = await user_client.client.get(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
    )

    assert first_comment["ticket_id"] == ticket.id
    assert [comment["text"] for comment in list_response.json()] == [
        "First comment",
        "Second comment",
    ]


async def test_user_cannot_comment_on_another_users_ticket(
    user_client: AuthenticatedClient,
    user_factory: Callable[[str, UserRole], User],
    ticket_factory: Callable[..., Ticket],
) -> None:
    other_user = user_factory("other@example.com", UserRole.USER)
    ticket = ticket_factory(other_user)
    response = await user_client.client.post(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
        json={"text": "Not allowed"},
    )

    assert response.status_code == 404

    list_response = await user_client.client.get(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
    )
    assert list_response.status_code == 404


async def test_support_comments_on_any_ticket(
    support_client: AuthenticatedClient,
    user: User,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user)
    comment = await create_comment(support_client, ticket.id, "Support reply")

    assert comment["author_id"] == support_client.user.id
    assert comment["text"] == "Support reply"


async def test_user_edits_own_comment(
    user_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    comment = await create_comment(user_client, ticket.id)
    response = await user_client.client.patch(
        f"/comments/{comment['id']}",
        headers=user_client.headers,
        json={"text": "Updated comment"},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Updated comment"


async def test_user_cannot_edit_another_users_comment(
    user_client: AuthenticatedClient,
    support_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    comment = await create_comment(support_client, ticket.id)
    response = await user_client.client.patch(
        f"/comments/{comment['id']}",
        headers=user_client.headers,
        json={"text": "Not allowed"},
    )

    assert response.status_code == 403


async def test_user_cannot_edit_comment_in_foreign_ticket(
    user_client: AuthenticatedClient,
    support_client: AuthenticatedClient,
    user_factory: Callable[[str, UserRole], User],
    ticket_factory: Callable[..., Ticket],
) -> None:
    other_user = user_factory("other@example.com", UserRole.USER)
    ticket = ticket_factory(other_user)
    comment = await create_comment(support_client, ticket.id)

    response = await user_client.client.patch(
        f"/comments/{comment['id']}",
        headers=user_client.headers,
        json={"text": "Not allowed"},
    )

    assert response.status_code == 404


async def test_support_and_admin_delete_comments(
    support_client: AuthenticatedClient,
    admin_client: AuthenticatedClient,
    user: User,
    ticket_factory: Callable[..., Ticket],
    comment_factory: Callable[[Ticket, User, str], Comment],
) -> None:
    ticket = ticket_factory(user)
    support_comment = comment_factory(ticket, user, "Support may delete")
    admin_comment = comment_factory(ticket, user, "Admin may delete")

    support_response = await support_client.client.delete(
        f"/comments/{support_comment.id}",
        headers=support_client.headers,
    )
    admin_response = await admin_client.client.delete(
        f"/comments/{admin_comment.id}",
        headers=admin_client.headers,
    )

    assert support_response.status_code == 204
    assert admin_response.status_code == 204


async def test_user_cannot_delete_comments(
    user_client: AuthenticatedClient,
    support_client: AuthenticatedClient,
    user_factory: Callable[[str, UserRole], User],
    ticket_factory: Callable[..., Ticket],
) -> None:
    own_ticket = ticket_factory(user_client.user)
    own_comment = await create_comment(user_client, own_ticket.id)
    other_user = user_factory("other@example.com", UserRole.USER)
    foreign_ticket = ticket_factory(other_user)
    foreign_comment = await create_comment(support_client, foreign_ticket.id)

    own_response = await user_client.client.delete(
        f"/comments/{own_comment['id']}",
        headers=user_client.headers,
    )
    foreign_response = await user_client.client.delete(
        f"/comments/{foreign_comment['id']}",
        headers=user_client.headers,
    )

    assert own_response.status_code == 403
    assert foreign_response.status_code == 404


async def test_comment_requires_text(
    user_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    response = await user_client.client.post(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
        json={},
    )

    assert response.status_code == 422


async def test_comment_rejects_blank_and_unknown_fields(
    user_client: AuthenticatedClient,
    ticket_factory: Callable[..., Ticket],
) -> None:
    ticket = ticket_factory(user_client.user)
    blank_response = await user_client.client.post(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
        json={"text": "   "},
    )
    unknown_response = await user_client.client.post(
        f"/tickets/{ticket.id}/comments",
        headers=user_client.headers,
        json={"text": "Valid", "author_id": 999},
    )

    assert blank_response.status_code == 422
    assert unknown_response.status_code == 422
