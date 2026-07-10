from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.models.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import TicketCreate, TicketListItem, TicketRead, TicketUpdate
from app.services.tickets import (
    create_ticket,
    delete_ticket,
    get_ticket_for_user,
    list_tickets,
    update_ticket,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_new_ticket(
    ticket_data: TicketCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> TicketRead:
    """Create a support ticket for the current user."""
    return create_ticket(db, ticket_data, current_user)


@router.get("", response_model=list[TicketListItem])
def read_tickets(
    db: DbSession,
    current_user: CurrentUser,
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    author_id: Annotated[int | None, Query(gt=0)] = None,
    assigned_to_id: Annotated[int | None, Query(gt=0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TicketListItem]:
    """List tickets available to the current user."""
    return list_tickets(
        db,
        current_user,
        ticket_status=ticket_status,
        priority=priority,
        author_id=author_id,
        assigned_to_id=assigned_to_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{ticket_id}", response_model=TicketRead)
def read_ticket(
    ticket_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> TicketRead:
    """Get a ticket by ID when it is visible to the current user."""
    return get_ticket_for_user(db, ticket_id, current_user)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_existing_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TicketRead:
    """Partially update a ticket with role-specific permissions."""
    ticket = get_ticket_for_user(db, ticket_id, current_user)
    return update_ticket(db, ticket, ticket_data, current_user)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_ticket(
    ticket_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    """Delete a ticket as an administrator."""
    ticket = get_ticket_for_user(db, ticket_id, current_user)
    delete_ticket(db, ticket, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
