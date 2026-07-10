from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services.comments import (
    create_comment,
    delete_comment,
    get_comment_or_404,
    list_comments,
    update_comment,
)
from app.services.tickets import get_ticket_for_user

router = APIRouter(tags=["comments"])


@router.post(
    "/tickets/{ticket_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_comment(
    ticket_id: int,
    comment_data: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> CommentRead:
    """Add a comment to a ticket visible to the current user."""
    ticket = get_ticket_for_user(db, ticket_id, current_user)
    return create_comment(db, ticket, comment_data, current_user)


@router.get("/tickets/{ticket_id}/comments", response_model=list[CommentRead])
def read_ticket_comments(
    ticket_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[CommentRead]:
    """Return comments for a ticket visible to the current user."""
    ticket = get_ticket_for_user(db, ticket_id, current_user)
    return list_comments(db, ticket)


@router.patch("/comments/{comment_id}", response_model=CommentRead)
def update_existing_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> CommentRead:
    """Edit the current user's own comment."""
    comment = get_comment_or_404(db, comment_id)
    return update_comment(db, comment, comment_data, current_user)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_comment(
    comment_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    """Delete a comment as support staff or an administrator."""
    comment = get_comment_or_404(db, comment_id)
    delete_comment(db, comment, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
