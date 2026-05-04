from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.city import CityOrder
from app.domain.ride_statuses import RideStatus

async def accept_order(db: AsyncSession, order_id: int, driver_id: int):
    async with db.begin():
        # Хирургическая блокировка строки заказа (Race Condition Protection)
        stmt = select(CityOrder).filter(CityOrder.id == order_id).with_for_update()
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order or order.status != RideStatus.SEARCHING:
            return {"status": "error", "message": "ORDER_ALREADY_TAKEN"}
            
        order.driver_id = driver_id
        order.status = RideStatus.ACCEPTED
        order.accepted_at = datetime.utcnow()
        return {"status": "success", "order_id": order.id}