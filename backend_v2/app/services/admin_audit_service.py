from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminAuditLog
from app.models.base_mixins import utcnow
from app.models.user import User


class AdminAuditService:
    async def write(
        self,
        session: AsyncSession,
        *,
        admin: User,
        action: str,
        entity_type: str,
        entity_id: str | int,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AdminAuditLog:
        row = AdminAuditLog(
            admin_user_id=admin.id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            before_json=before,
            after_json=after,
            ip_address=ip_address,
            created_at=utcnow(),
        )
        session.add(row)
        await session.flush()
        return row
