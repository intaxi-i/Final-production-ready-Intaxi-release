import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from app.core.database import AsyncSessionLocal
from app.models.driver import DriverOnlineState

logger = logging.getLogger(__name__)

async def reset_offline_drivers_task(timeout_minutes: int = 5, interval_seconds: int = 60):
    while True:
        try:
            async with AsyncSessionLocal() as session:
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
                stmt = (
                    update(DriverOnlineState)
                    .where(DriverOnlineState.is_online == True)
                    .where(DriverOnlineState.updated_at < cutoff_time)
                    .values(is_online=False)
                )
                result = await session.execute(stmt)
                await session.commit()
                if result.rowcount > 0:
                    logger.info(f"[HEARTBEAT] Сброс статуса в 'офлайн' для {result.rowcount} водителей (превышен лимит {timeout_minutes} мин).")
        except Exception as e:
            logger.error(f"[HEARTBEAT] Ошибка транзакции при обновлении статусов: {e}")
        await asyncio.sleep(interval_seconds)
