from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.comment import Comment


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


ticket_status_enum = SqlEnum(
    TicketStatus,
    name="ticket_status",
    values_callable=lambda enum_class: [status.value for status in enum_class],
)
ticket_priority_enum = SqlEnum(
    TicketPriority,
    name="ticket_priority",
    values_callable=lambda enum_class: [priority.value for priority in enum_class],
)


class Ticket(Base):
    """Technical support request created by a user."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(
        ticket_status_enum,
        default=TicketStatus.OPEN,
        server_default=TicketStatus.OPEN.value,
        index=True,
    )
    priority: Mapped[TicketPriority] = mapped_column(
        ticket_priority_enum,
        default=TicketPriority.MEDIUM,
        server_default=TicketPriority.MEDIUM.value,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    author: Mapped[User] = relationship(
        back_populates="authored_tickets",
        foreign_keys=[author_id],
    )
    assigned_to: Mapped[User | None] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[assigned_to_id],
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )
