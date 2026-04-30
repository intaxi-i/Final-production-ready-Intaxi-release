from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.errors import raise_domain
from app.models.support import SupportTicket
from app.models.user import User
from app.schemas.support import SupportTicketCreate, SupportTicketRead, SupportTicketUpdate
from app.services.admin_audit_service import AdminAuditService

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/tickets", response_model=SupportTicketRead)
async def create_support_ticket(
    payload: SupportTicketCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupportTicketRead:
    if current_user.is_blocked:
        raise_domain("user_blocked", "Blocked user cannot create support ticket", 403)
    row = SupportTicket(
        created_by_user_id=current_user.id,
        related_type=payload.related_type,
        related_id=payload.related_id,
        ticket_type=payload.ticket_type,
        priority=payload.priority,
        status="open",
        subject=payload.subject,
        message=payload.message,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return SupportTicketRead.model_validate(row)


@router.get("/tickets/my", response_model=list[SupportTicketRead])
async def my_support_tickets(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SupportTicketRead]:
    rows = (
        await session.scalars(
            select(SupportTicket)
            .where(SupportTicket.created_by_user_id == current_user.id)
            .order_by(SupportTicket.id.desc())
            .limit(100)
        )
    ).all()
    return [SupportTicketRead.model_validate(row) for row in rows]


@router.get("/admin/tickets", response_model=list[SupportTicketRead])
async def admin_support_tickets(
    status: str | None = None,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[SupportTicketRead]:
    query = select(SupportTicket).order_by(SupportTicket.id.desc()).limit(200)
    if status:
        query = select(SupportTicket).where(SupportTicket.status == status).order_by(SupportTicket.id.desc()).limit(200)
    rows = (await session.scalars(query)).all()
    return [SupportTicketRead.model_validate(row) for row in rows]


@router.patch("/admin/tickets/{ticket_id}", response_model=SupportTicketRead)
async def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> SupportTicketRead:
    row = await session.scalar(select(SupportTicket).where(SupportTicket.id == ticket_id))
    if not row:
        raise_domain("support_ticket_not_found", "Support ticket not found", 404)
    before = {"status": row.status, "assigned_admin_id": row.assigned_admin_id, "admin_notes": row.admin_notes}
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"]:
        row.status = data["status"]
        if data["status"] in {"closed", "resolved"}:
            row.closed_at = datetime.now(timezone.utc)
    if "assigned_admin_id" in data:
        row.assigned_admin_id = data["assigned_admin_id"]
    if "admin_notes" in data:
        row.admin_notes = data["admin_notes"]
    await session.flush()
    after = {"status": row.status, "assigned_admin_id": row.assigned_admin_id, "admin_notes": row.admin_notes}
    await AdminAuditService().write(
        session,
        admin=admin,
        action="support_ticket.update",
        entity_type="support_ticket",
        entity_id=row.id,
        before=before,
        after=after,
    )
    await session.commit()
    await session.refresh(row)
    return SupportTicketRead.model_validate(row)
