from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commission import CommissionRule


@dataclass(frozen=True, slots=True)
class CommissionDecision:
    percent: float
    rule_id: int | None
    free_first_rides: int


class CommissionService:
    async def resolve_commission(
        self,
        session: AsyncSession,
        *,
        country_code: str | None,
        city_id: int | None,
        driver_user_id: int | None,
    ) -> CommissionDecision:
        now = datetime.now(timezone.utc)
        candidates: list[tuple[str, str]] = []
        if driver_user_id is not None:
            candidates.append(("driver", str(driver_user_id)))
        if city_id is not None:
            candidates.append(("city", str(city_id)))
        if country_code:
            candidates.append(("country", country_code.lower()))
        candidates.append(("global", "global"))

        for scope_type, scope_id in candidates:
            rule = await session.scalar(
                select(CommissionRule)
                .where(
                    CommissionRule.scope_type == scope_type,
                    CommissionRule.scope_id == scope_id,
                    CommissionRule.is_active == True,
                )
                .order_by(CommissionRule.id.desc())
            )
            if not rule:
                continue
            if rule.starts_at and rule.starts_at > now:
                continue
            if rule.ends_at and rule.ends_at < now:
                continue
            return CommissionDecision(
                percent=float(rule.commission_percent or 0),
                rule_id=rule.id,
                free_first_rides=int(rule.free_first_rides or 0),
            )
        return CommissionDecision(percent=0.0, rule_id=None, free_first_rides=0)

    def calculate_commission_amount(self, final_price: float, percent: float) -> float:
        if percent <= 0:
            return 0.0
        return round(float(final_price) * float(percent) / 100, 2)
