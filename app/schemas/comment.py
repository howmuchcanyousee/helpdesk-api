from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

CommentText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5_000),
]


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: CommentText


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: int
    text: str
    created_at: datetime
    updated_at: datetime


class CommentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: CommentText
