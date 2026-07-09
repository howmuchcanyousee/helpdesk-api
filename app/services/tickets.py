from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate


def create_ticket(db: Session, ticket_data: TicketCreate, author: User) -> Ticket:
    """Create a ticket authored by the current user."""
    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        author_id=author.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    """Return a ticket or raise a not-found error."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


def get_ticket_for_user(db: Session, ticket_id: int, current_user: User) -> Ticket:
    """Return a ticket only when the current user is allowed to view it."""
    ticket = get_ticket_or_404(db, ticket_id)
    if current_user.role is UserRole.USER and ticket.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


def list_tickets(
    db: Session,
    current_user: User,
    *,
    ticket_status: TicketStatus | None,
    priority: TicketPriority | None,
    author_id: int | None,
    assigned_to_id: int | None,
    limit: int,
    offset: int,
) -> list[Ticket]:
    """Return tickets visible to the current user with optional filters."""
    statement = select(Ticket)

    if current_user.role is UserRole.USER:
        statement = statement.where(Ticket.author_id == current_user.id)
    if author_id is not None:
        statement = statement.where(Ticket.author_id == author_id)
    if ticket_status is not None:
        statement = statement.where(Ticket.status == ticket_status)
    if priority is not None:
        statement = statement.where(Ticket.priority == priority)
    if assigned_to_id is not None:
        statement = statement.where(Ticket.assigned_to_id == assigned_to_id)

    statement = statement.order_by(Ticket.created_at.desc(), Ticket.id.desc())
    statement = statement.offset(offset).limit(limit)
    return list(db.scalars(statement))


def update_ticket(
    db: Session,
    ticket: Ticket,
    ticket_data: TicketUpdate,
    current_user: User,
) -> Ticket:
    """Update fields allowed for the current user's role."""
    updates = ticket_data.model_dump(exclude_unset=True)
    if not updates:
        return ticket

    _ensure_update_permission(ticket, updates, current_user)
    _ensure_assignee_exists(db, updates)

    for field_name, value in updates.items():
        setattr(ticket, field_name, value)

    db.commit()
    db.refresh(ticket)
    return ticket


def delete_ticket(db: Session, ticket: Ticket, current_user: User) -> None:
    """Delete a ticket when requested by an administrator."""
    if current_user.role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tickets",
        )

    db.delete(ticket)
    db.commit()


def _ensure_update_permission(
    ticket: Ticket,
    updates: dict[str, object],
    current_user: User,
) -> None:
    if current_user.role is UserRole.ADMIN:
        return

    if current_user.role is UserRole.SUPPORT:
        _ensure_allowed_fields(updates, {"status", "assigned_to_id"})
        return

    if ticket.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    if ticket.status is TicketStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Closed tickets cannot be edited",
        )
    _ensure_allowed_fields(updates, {"title", "description"})


def _ensure_allowed_fields(
    updates: dict[str, object], allowed_fields: set[str]
) -> None:
    if not updates.keys() <= allowed_fields:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update these ticket fields",
        )


def _ensure_assignee_exists(db: Session, updates: dict[str, object]) -> None:
    assigned_to_id = updates.get("assigned_to_id")
    if assigned_to_id is not None and db.get(User, assigned_to_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found",
        )
