from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_mixins import TimestampMixin


class CommissionRule(TimestampMixin, Base):
    __tablename__ = "commission_rules_v2"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    commission_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    free_first_rides: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
    updated_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users_v2.id"))
