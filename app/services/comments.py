from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate, CommentUpdate


def create_comment(
    db: Session,
    ticket: Ticket,
    comment_data: CommentCreate,
    author: User,
) -> Comment:
    """Create a comment in a ticket visible to the current user."""
    comment = Comment(
        ticket_id=ticket.id,
        author_id=author.id,
        text=comment_data.text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, ticket: Ticket) -> list[Comment]:
    """Return a ticket discussion in chronological order."""
    statement = (
        select(Comment)
        .where(Comment.ticket_id == ticket.id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    return list(db.scalars(statement))


def get_comment_or_404(db: Session, comment_id: int) -> Comment:
    """Return a comment or raise a not-found error."""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return comment


def update_comment(
    db: Session,
    comment: Comment,
    comment_data: CommentUpdate,
    current_user: User,
) -> Comment:
    """Update a comment when it belongs to the current user."""
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    comment.text = comment_data.text
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment, current_user: User) -> None:
    """Delete a comment when requested by support or an administrator."""
    if current_user.role not in {UserRole.SUPPORT, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support staff and administrators can delete comments",
        )

    db.delete(comment)
    db.commit()
