from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from app.models.ticket import TicketPriority, TicketStatus

TicketTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
TicketDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000),
]


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle
    description: TicketDescription
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    author_id: int
    assigned_to_id: int | None
    created_at: datetime
    updated_at: datetime


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TicketTitle | None = None
    description: TicketDescription | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to_id: int | None = Field(default=None, gt=0)

    @field_validator("title", "description", "status", "priority")
    @classmethod
    def reject_null_for_required_columns(cls, value: object) -> object:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class TicketListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TicketStatus
    priority: TicketPriority
    author_id: int
    assigned_to_id: int | None
    created_at: datetime
    updated_at: datetime
