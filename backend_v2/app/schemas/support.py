from __future__ import annotations

from pydantic import BaseModel, Field


class SupportTicketCreate(BaseModel):
    ticket_type: str = "general"
    priority: str = "normal"
    related_type: str | None = None
    related_id: int | None = None
    subject: str | None = None
    message: str = Field(min_length=1)


class SupportTicketUpdate(BaseModel):
    status: str | None = None
    assigned_admin_id: int | None = None
    admin_notes: str | None = None


class SupportTicketRead(BaseModel):
    id: int
    created_by_user_id: int
    assigned_admin_id: int | None = None
    related_type: str | None = None
    related_id: int | None = None
    ticket_type: str
    priority: str
    status: str
    subject: str | None = None
    message: str
    admin_notes: str | None = None

    model_config = {"from_attributes": True}
