from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users_v2.id"), index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
