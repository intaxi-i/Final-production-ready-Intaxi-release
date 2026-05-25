from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from api.auth import get_current_user
from api.schemas import *
from api.services import city as city_service
from intaxi_bot.app.database.models import AdminRole, CityOrderRuntime, CityOrderV1, CityTripV1, IntercityRequestV1, IntercityRouteMeta, IntercityRouteV1, User, async_session, utcnow

router = APIRouter()


async def rq_get_admin_role(tg_id: int):
    async with async_session() as session:
        rows = (await session.scalars(select(AdminRole.role).where(AdminRole.tg_id == tg_id, AdminRole.is_active == True))).all()
        for role in ('superadmin','admin','moderator','finance'):
            if role in rows:
                return role
        return None

@router.get('/city/tariffs', response_model=TariffListResponse)
async def city_tariffs(current_user: User = Depends(get_current_user)) -> TariffListResponse:
    return await city_service.list_tariffs()

@router.get('/admin/tariffs', response_model=TariffListResponse)
async def admin_tariffs(current_user: User = Depends(get_current_user)) -> TariffListResponse:
    if await rq_get_admin_role(current_user.tg_id) != 'superadmin': raise HTTPException(status_code=403, detail='Forbidden')
    return await city_service.list_tariffs()

@router.post('/city/orders', response_model=CityOrderCreateResponse)
async def create_city_order(payload: CityOrderCreateRequest, current_user: User = Depends(get_current_user)) -> CityOrderCreateResponse:
    return await city_service.create_city_order(payload, current_user)

@router.get('/city/offers', response_model=CityOrderListResponse)
async def city_offers(kind: str = Query('all'), current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    return await city_service.city_offers(kind, current_user)

@router.get('/city/offers/{order_id}', response_model=CityOrderEnvelope)
async def city_offer_detail(order_id: int, current_user: User = Depends(get_current_user)) -> CityOrderEnvelope:
    row = await city_service.get_city_offer_detail(order_id, current_user)
    return CityOrderEnvelope(item=row)

@router.get('/city/my-orders', response_model=CityOrderListResponse)
async def city_my_orders(current_user: User = Depends(get_current_user)) -> CityOrderListResponse:
    return await city_service.city_my_orders(current_user)

@router.post('/city/orders/{order_id}/close')
async def city_close(order_id: int, current_user: User = Depends(get_current_user)) -> dict:
    return await city_service.city_close(order_id, current_user)

@router.post('/city/orders/{order_id}/raise-price')
async def city_raise_price(order_id: int, payload: RaisePriceRequest, current_user: User = Depends(get_current_user)) -> dict:
    return await city_service.city_raise_price(order_id, payload, current_user)

@router.post('/city/offers/{order_id}/accept', response_model=CityAcceptResponse)
async def city_accept(order_id: int, current_user: User = Depends(get_current_user)) -> CityAcceptResponse:
    return await city_service.city_accept(order_id, current_user)

@router.get('/city/trips/{trip_id}', response_model=CityTripEnvelope)
async def city_trip_detail(trip_id: int, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    trip = await city_service.city_trip_detail(trip_id, current_user)
    return CityTripEnvelope(item=trip)

@router.post('/city/trips/{trip_id}/status', response_model=CityTripEnvelope)
async def city_trip_status(trip_id: int, payload: CityTripStatusUpdateRequest, current_user: User = Depends(get_current_user)) -> CityTripEnvelope:
    return CityTripEnvelope(item=await city_service.city_trip_status(trip_id, payload, current_user))

@router.get('/trip/current', response_model=CurrentTripResponse)
async def current_trip(current_user: User = Depends(get_current_user)) -> CurrentTripResponse:
    return await city_service.current_trip(current_user)
