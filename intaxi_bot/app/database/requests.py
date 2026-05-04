from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select

from .models import (
    AdminRole,
    ChatMessageV1,
    CityOrderRuntime,
    CityOrderV1,
    CityTripV1,
    DriverOnlineState,
    DriverPaymentRequest,
    FeedbackEntry,
    IntercityRequestV1,
    IntercityRouteMeta,
    IntercityRouteV1,
    MessageCleanup,
    TariffSetting,
    User,
    Vehicle,
    async_session,
)

ROLE_PERMISSIONS = {
    'superadmin': {'dashboard', 'users', 'drivers', 'finance', 'orders', 'moderation', 'broadcast', 'payments', 'lookup', 'feedback', 'complaints', 'admins'},
    'admin': {'dashboard', 'users', 'drivers', 'orders', 'moderation', 'feedback', 'complaints', 'lookup', 'payments'},
    'moderator': {'dashboard', 'moderation', 'feedback', 'complaints', 'drivers'},
    'finance': {'dashboard', 'finance', 'payments', 'lookup'},
}
DEFAULT_TARIFFS = {
    'uz': ('UZS', 2500.0),
    'tr': ('TRY', 45.0),
    'sa': ('SAR', 2.5),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _bootstrap_superadmins() -> list[int]:
    raw = os.getenv('SUPERADMIN_IDS', '').strip()
    items: list[int] = []
    if raw:
        for part in raw.split(','):
            part = part.strip()
            if part.isdigit():
                items.append(int(part))
    if not items:
        items.append(89137224)
    return items


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def ensure_bootstrap_superadmins() -> None:
    async with async_session() as session:
        for tg_id in _bootstrap_superadmins():
            row = await session.scalar(select(AdminRole).where(AdminRole.tg_id == tg_id, AdminRole.role == 'superadmin'))
            if not row:
                session.add(AdminRole(tg_id=tg_id, role='superadmin', is_active=True, assigned_by=tg_id))
        for country, (currency, value) in DEFAULT_TARIFFS.items():
            row = await session.scalar(select(TariffSetting).where(TariffSetting.country == country))
            if not row:
                session.add(TariffSetting(country=country, currency=currency, price_per_km=value))
        await session.commit()


async def get_or_create_user(tg_id: int, full_name: str = '', username: str | None = None) -> User:
    await ensure_bootstrap_superadmins()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id, full_name=full_name or '', username=username, active_role='passenger', free_rides_left=0)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            changed = False
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                changed = True
            if username is not None and user.username != username:
                user.username = username
                changed = True
            if changed:
                await session.commit()
                await session.refresh(user)
        return user


async def set_user_reg(tg_id: int, language: str, country: str, city: str) -> User:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id)
            session.add(user)
        user.language = language or user.language or 'ru'
        user.country = country
        user.city = city
        await session.commit()
        await session.refresh(user)
        return user


async def update_user_language(tg_id: int, language: str) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.language = language
        await session.commit()
        await session.refresh(user)
        return user


async def update_user_country_city(tg_id: int, country: str, city: str) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.country = country
        user.city = city
        await session.commit()
        await session.refresh(user)
        return user


async def _active_roles(tg_id: int) -> list[str]:
    async with async_session() as session:
        rows = (await session.scalars(select(AdminRole.role).where(AdminRole.tg_id == tg_id, AdminRole.is_active == True))).all()
        return list(rows)


async def get_admin_role(tg_id: int) -> str | None:
    roles = await _active_roles(tg_id)
    for role in ('superadmin', 'admin', 'moderator', 'finance'):
        if role in roles:
            return role
    return None


async def is_admin_user(tg_id: int) -> bool:
    return (await get_admin_role(tg_id)) is not None


async def admin_has_permission(tg_id: int, permission: str) -> bool:
    roles = await _active_roles(tg_id)
    for role in roles:
        if permission in ROLE_PERMISSIONS.get(role, set()):
            return True
    return False


async def get_admin_targets_by_permission(permission: str) -> list[int]:
    await ensure_bootstrap_superadmins()
    async with async_session() as session:
        rows = (await session.scalars(select(AdminRole).where(AdminRole.is_active == True))).all()
    result: list[int] = []
    for row in rows:
        if permission in ROLE_PERMISSIONS.get(row.role, set()) and row.tg_id not in result:
            result.append(row.tg_id)
    return result


async def list_admin_roles() -> list[AdminRole]:
    await ensure_bootstrap_superadmins()
    async with async_session() as session:
        rows = (await session.scalars(select(AdminRole).where(AdminRole.is_active == True).order_by(AdminRole.role, AdminRole.tg_id))).all()
        return list(rows)


async def count_active_admins_by_role(role: str) -> int:
    async with async_session() as session:
        value = await session.scalar(select(func.count()).select_from(AdminRole).where(AdminRole.role == role, AdminRole.is_active == True)) or 0
        return int(value)


async def set_admin_role(target_tg_id: int, role: str, assigned_by: int | None = None) -> AdminRole:
    if role not in ROLE_PERMISSIONS:
        raise ValueError('Unsupported role')
    await ensure_bootstrap_superadmins()
    async with async_session() as session:
        existing = await session.scalar(select(AdminRole).where(AdminRole.tg_id == target_tg_id, AdminRole.role == role))
        if existing:
            existing.is_active = True
            existing.assigned_by = assigned_by
            await session.commit()
            await session.refresh(existing)
            return existing
        row = AdminRole(tg_id=target_tg_id, role=role, is_active=True, assigned_by=assigned_by)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def revoke_admin_roles(target_tg_id: int) -> int:
    async with async_session() as session:
        rows = (await session.scalars(select(AdminRole).where(AdminRole.tg_id == target_tg_id, AdminRole.is_active == True))).all()
        count = 0
        for row in rows:
            row.is_active = False
            count += 1
        await session.commit()
        return count


async def register_vehicle(tg_id: int, data: dict[str, Any]) -> Vehicle:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            user = User(tg_id=tg_id, active_role='passenger')
            session.add(user)
            await session.flush()
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
        capacity_value = str(data.get('capacity') or '4')
        vehicle_class = 'class7' if '6' in capacity_value or '8' in capacity_value else 'class4'
        accepts_class7 = vehicle_class == 'class7'
        payload = dict(
            brand=str(data.get('brand') or ''),
            model=str(data.get('model') or ''),
            plate=str(data.get('plate') or ''),
            color=str(data.get('color') or ''),
            capacity=capacity_value,
            vehicle_class=vehicle_class,
            accepts_class4=True,
            accepts_class7=accepts_class7,
            photo_tech=data.get('photo_tech'), photo_license=data.get('photo_license'), photo_out=data.get('photo_out'), photo_in=data.get('photo_in'),
            photo_tech_path=data.get('photo_tech_path'), photo_license_path=data.get('photo_license_path'), photo_out_path=data.get('photo_out_path'), photo_in_path=data.get('photo_in_path'),
        )
        if vehicle:
            for key, value in payload.items():
                setattr(vehicle, key, value)
        else:
            vehicle = Vehicle(user_id=user.id, **payload)
            session.add(vehicle)
        user.active_role = 'passenger'
        user.is_verified = False
        await session.commit()
        await session.refresh(vehicle)
        return vehicle


async def set_driver_card(tg_id: int, card_country: str | None, card_number: str | None) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.driver_card_country = card_country
        user.driver_card_number = card_number
        await session.commit()
        await session.refresh(user)
        return user


async def verify_driver(user_tg_id: int) -> User | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_tg_id))
        if not user:
            return None
        user.is_verified = True
        user.active_role = 'driver'
        await session.commit()
        await session.refresh(user)
        return user


async def reject_user_vehicle(user_tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_tg_id))
        if not user:
            return False
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
        if vehicle:
            await session.delete(vehicle)
        user.is_verified = False
        user.active_role = 'passenger'
        await session.commit()
        return True


async def remove_vehicle_for_edit(tg_id: int) -> bool:
    return await reject_user_vehicle(tg_id)


async def toggle_driver_accepts_class4(tg_id: int) -> Vehicle | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == user.id))
        if not vehicle:
            return None
        vehicle.accepts_class4 = not bool(vehicle.accepts_class4)
        await session.commit()
        await session.refresh(vehicle)
        return vehicle


async def set_user_active_role(tg_id: int, new_role: str) -> User | None:
    if new_role not in {'driver', 'passenger'}:
        return None
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        user.active_role = new_role
        await session.commit()
        await session.refresh(user)
        return user


async def create_driver_payment_request(driver_tg_id: int, card_country: str | None, admin_card_number: str | None, amount: float, receipt_file_id: str | None):
    async with async_session() as session:
        row = DriverPaymentRequest(driver_tg_id=driver_tg_id, card_country=card_country, admin_card_number=admin_card_number, amount=float(amount or 0), receipt_file_id=receipt_file_id, status='pending')
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def update_driver_payment_request_amount(request_id: int, amount: float) -> DriverPaymentRequest | None:
    async with async_session() as session:
        row = await session.scalar(select(DriverPaymentRequest).where(DriverPaymentRequest.id == request_id, DriverPaymentRequest.status == 'pending').with_for_update())
        if not row:
            return None
        row.amount = float(amount)
        await session.commit()
        await session.refresh(row)
        return row


async def approve_driver_payment_request(request_id: int, reviewed_by: int | None = None):
    async with async_session() as session:
        req = await session.scalar(select(DriverPaymentRequest).where(DriverPaymentRequest.id == request_id, DriverPaymentRequest.status == 'pending').with_for_update())
        if not req:
            return None
        user = await session.scalar(select(User).where(User.tg_id == req.driver_tg_id).with_for_update())
        if not user:
            return None
        user.balance = float(user.balance or 0) + float(req.amount or 0)
        req.status = 'approved'
        req.reviewed_by = reviewed_by
        req.reviewed_at = _now()
        await session.commit()
        await session.refresh(req)
        await session.refresh(user)
        return req, user


async def reject_driver_payment_request(request_id: int, reviewed_by: int | None = None):
    async with async_session() as session:
        req = await session.scalar(select(DriverPaymentRequest).where(DriverPaymentRequest.id == request_id, DriverPaymentRequest.status == 'pending').with_for_update())
        if not req:
            return None
        user = await session.scalar(select(User).where(User.tg_id == req.driver_tg_id).with_for_update())
        req.status = 'rejected'
        req.reviewed_by = reviewed_by
        req.reviewed_at = _now()
        await session.commit()
        if user:
            await session.refresh(user)
        return req, user


async def estimate_driver_rides_left(tg_id: int) -> int | None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user or not user.is_verified:
            return None
        return 0


def get_map_link(value: str | None) -> str | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if "," in raw:
        parts = [x.strip() for x in raw.split(",", 1)]
        try:
            lat = float(parts[0])
            lng = float(parts[1])
            return f"https://maps.google.com/?q={lat},{lng}"
        except Exception:
            pass
    from urllib.parse import quote_plus
    return f"https://maps.google.com/?q={quote_plus(raw)}"


async def create_feedback_entry(user_tg_id: int, kind: str, content_type: str, *, text_value: str | None = None, file_id: str | None = None):
    async with async_session() as session:
        row = FeedbackEntry(user_tg_id=user_tg_id, kind=kind, content_type=content_type, text_value=text_value, file_id=file_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def track_cleanup_message(user_tg_id: int, chat_id: int, message_id: int, context: str = 'admin') -> None:
    async with async_session() as session:
        existing = await session.scalar(select(MessageCleanup).where(MessageCleanup.user_tg_id == user_tg_id, MessageCleanup.message_id == message_id))
        if not existing:
            session.add(MessageCleanup(user_tg_id=user_tg_id, chat_id=chat_id, message_id=message_id, context=context))
            await session.commit()


async def get_cleanup_messages(user_tg_id: int, context: str = 'admin') -> list[MessageCleanup]:
    async with async_session() as session:
        rows = (await session.scalars(select(MessageCleanup).where(MessageCleanup.user_tg_id == user_tg_id, MessageCleanup.context == context).order_by(MessageCleanup.id.desc()))).all()
        return list(rows)


async def clear_cleanup_messages(user_tg_id: int, context: str = 'admin') -> None:
    async with async_session() as session:
        await session.execute(delete(MessageCleanup).where(MessageCleanup.user_tg_id == user_tg_id, MessageCleanup.context == context))
        await session.commit()


async def get_basic_stats() -> dict[str, int]:
    async with async_session() as session:
        users = await session.scalar(select(func.count()).select_from(User)) or 0
        drivers = await session.scalar(select(func.count()).select_from(User).where(User.is_verified == True)) or 0
        pending_payments = await session.scalar(select(func.count()).select_from(DriverPaymentRequest).where(DriverPaymentRequest.status == 'pending')) or 0
        pending_feedback = await session.scalar(select(func.count()).select_from(FeedbackEntry)) or 0
        active_city = await session.scalar(select(func.count()).select_from(CityOrderV1).where(CityOrderV1.status == 'active')) or 0
        active_routes = await session.scalar(select(func.count()).select_from(IntercityRouteV1).where(IntercityRouteV1.status == 'active')) or 0
        active_requests = await session.scalar(select(func.count()).select_from(IntercityRequestV1).where(IntercityRequestV1.status == 'active')) or 0
        return {'users': int(users), 'drivers': int(drivers), 'pending_payments': int(pending_payments), 'feedback': int(pending_feedback), 'active_city': int(active_city), 'active_routes': int(active_routes), 'active_requests': int(active_requests)}


async def list_recent_users(limit: int = 10) -> list[User]:
    async with async_session() as session:
        rows = (await session.scalars(select(User).order_by(User.created_at.desc()).limit(limit))).all()
        return list(rows)


async def list_pending_driver_payments(limit: int = 10) -> list[DriverPaymentRequest]:
    async with async_session() as session:
        rows = (await session.scalars(select(DriverPaymentRequest).where(DriverPaymentRequest.status == 'pending').order_by(DriverPaymentRequest.created_at.desc()).limit(limit))).all()
        return list(rows)


async def list_recent_feedback(limit: int = 10) -> list[FeedbackEntry]:
    async with async_session() as session:
        rows = (await session.scalars(select(FeedbackEntry).order_by(FeedbackEntry.created_at.desc()).limit(limit))).all()
        return list(rows)


async def find_user_by_tg_id(tg_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def list_orders_snapshot(limit: int = 20) -> dict[str, list[Any]]:
    async with async_session() as session:
        city = (await session.scalars(select(CityOrderV1).where(CityOrderV1.status == 'active').order_by(CityOrderV1.id.desc()).limit(limit))).all()
        routes = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.status == 'active').order_by(IntercityRouteV1.id.desc()).limit(limit))).all()
        requests = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.status == 'active').order_by(IntercityRequestV1.id.desc()).limit(limit))).all()
        return {'city': list(city), 'routes': list(routes), 'requests': list(requests)}


async def cancel_city_order(order_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not row:
            return None
        row.status = 'cancelled_by_admin'
        await session.commit()
        await session.refresh(row)
        return row


async def cancel_intercity_route(route_id: int) -> IntercityRouteV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id))
        if not row:
            return None
        row.status = 'cancelled_by_admin'
        await session.commit()
        await session.refresh(row)
        return row


async def cancel_intercity_request(request_id: int) -> IntercityRequestV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id))
        if not row:
            return None
        row.status = 'cancelled_by_admin'
        await session.commit()
        await session.refresh(row)
        return row


async def get_current_trip_for_user(tg_id: int):
    async with async_session() as session:
        city_trip = await session.scalar(select(CityTripV1).where(((CityTripV1.passenger_tg_id == tg_id) | (CityTripV1.driver_tg_id == tg_id)), CityTripV1.status.in_(['accepted','driver_on_way','driver_arrived','in_progress'])).order_by(CityTripV1.id.desc()))
        if city_trip:
            return city_trip
        route = await session.scalar(select(IntercityRouteV1).where(((IntercityRouteV1.creator_tg_id == tg_id) | (IntercityRouteV1.accepted_by_tg_id == tg_id)), IntercityRouteV1.status.in_(['active','accepted','in_progress'])).order_by(IntercityRouteV1.id.desc()))
        if route:
            return route
        request = await session.scalar(select(IntercityRequestV1).where(((IntercityRequestV1.creator_tg_id == tg_id) | (IntercityRequestV1.accepted_by_tg_id == tg_id)), IntercityRequestV1.status.in_(['active','accepted','in_progress'])).order_by(IntercityRequestV1.id.desc()))
        return request


async def list_recent_complaints(limit: int = 10) -> list[FeedbackEntry]:
    async with async_session() as session:
        rows = (await session.scalars(select(FeedbackEntry).where(FeedbackEntry.kind == 'complaint').order_by(FeedbackEntry.created_at.desc()).limit(limit))).all()
        return list(rows)


async def close_city_order_for_user(order_id: int, tg_id: int) -> CityOrderV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id, CityOrderV1.creator_tg_id == tg_id))
        if not row:
            return None
        row.status = 'closed'
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
        if runtime and runtime.active_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == runtime.active_trip_id))
            if trip and trip.status not in {'completed', 'cancelled'}:
                trip.status = 'cancelled'
                trip.cancelled_at = _now()
        await session.commit()
        await session.refresh(row)
        return row


async def close_intercity_route_for_user(route_id: int, tg_id: int) -> IntercityRouteV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == route_id, IntercityRouteV1.creator_tg_id == tg_id))
        if not row:
            return None
        row.status = 'closed'
        await session.commit()
        await session.refresh(row)
        return row


async def close_intercity_request_for_user(request_id: int, tg_id: int) -> IntercityRequestV1 | None:
    async with async_session() as session:
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == request_id, IntercityRequestV1.creator_tg_id == tg_id))
        if not row:
            return None
        row.status = 'closed'
        await session.commit()
        await session.refresh(row)
        return row


async def _tariff_for_country(session, country: str | None) -> tuple[str, float]:
    normalized = (country or 'uz').strip().lower() or 'uz'
    row = await session.scalar(select(TariffSetting).where(TariffSetting.country == normalized))
    if row:
        return row.currency, float(row.price_per_km or 0)
    currency, value = DEFAULT_TARIFFS.get(normalized, ('USD', 0.0))
    return currency, float(value)


async def create_city_order_bot(*, creator_tg_id: int, role: str, country: str, city: str, from_address: str, to_address: str, seats: int = 1, price: float | None = None, comment: str = '', from_lat: float | None = None, from_lng: float | None = None, to_lat: float | None = None, to_lng: float | None = None) -> tuple[CityOrderV1, CityOrderRuntime]:
    if role not in {'driver', 'passenger'}:
        raise ValueError('Unsupported role')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == creator_tg_id))
        if not user:
            raise ValueError('User not found')
        if role == 'driver' and not user.is_verified:
            raise ValueError('Only verified drivers can create driver offers')
        currency, tariff_per_km = await _tariff_for_country(session, country)
        dist_km = None
        eta = None
        recommended_price = None
        if None not in {from_lat, from_lng, to_lat, to_lng}:
            dist_km = round(haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng)), 2)
            eta = max(1, int(round((dist_km / 28.0) * 60)))
            recommended_price = round(dist_km * tariff_per_km, 2)
        final_price = float(price) if price is not None and float(price) > 0 else recommended_price
        if final_price is None:
            raise ValueError('Price is required when distance cannot be calculated')
        order = CityOrderV1(creator_tg_id=creator_tg_id, role=role, country=country, city=city, from_address=from_address, to_address=to_address, seats=max(1, int(seats or 1)), price=final_price, comment=comment or '', status='active')
        session.add(order)
        await session.flush()
        seen = await session.scalar(select(func.count()).select_from(DriverOnlineState).where(DriverOnlineState.is_online == True, DriverOnlineState.country == country, DriverOnlineState.city == city)) or 0
        runtime = CityOrderRuntime(order_id=order.id, currency=currency, tariff_hint=f'{currency} {tariff_per_km}/km', recommended_price=recommended_price, system_price=recommended_price, from_lat=from_lat, from_lng=from_lng, to_lat=to_lat, to_lng=to_lng, estimated_distance_km=dist_km, estimated_trip_min=eta, dispatch_stage='bot', seen_by_drivers=int(seen))
        session.add(runtime)
        await session.commit()
        await session.refresh(order)
        await session.refresh(runtime)
        return order, runtime


async def list_city_market_for_user(tg_id: int, *, wanted_role: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    async with async_session() as session:
        current_user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not current_user:
            return []
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.status == 'active').order_by(CityOrderV1.id.desc()).limit(limit * 3))).all()
        result: list[dict[str, Any]] = []
        for row in rows:
            if row.creator_tg_id == tg_id:
                continue
            if wanted_role and row.role != wanted_role:
                continue
            if current_user.active_role == 'passenger' and row.role == 'driver' and current_user.is_verified is False:
                pass
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
            creator = await session.scalar(select(User).where(User.tg_id == row.creator_tg_id))
            vehicle = None
            if row.role == 'driver' and creator:
                vehicle = await session.scalar(select(Vehicle).where(Vehicle.user_id == creator.id))
            result.append({'order': row, 'runtime': runtime, 'creator': creator, 'vehicle': vehicle})
            if len(result) >= limit:
                break
        return result


async def list_user_city_orders(tg_id: int, limit: int = 10) -> list[dict[str, Any]]:
    async with async_session() as session:
        rows = (await session.scalars(select(CityOrderV1).where(CityOrderV1.creator_tg_id == tg_id).order_by(CityOrderV1.id.desc()).limit(limit))).all()
        result: list[dict[str, Any]] = []
        for row in rows:
            runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == row.id))
            result.append({'order': row, 'runtime': runtime})
        return result


async def accept_city_offer_for_user(order_id: int, tg_id: int) -> CityTripV1 | None:
    async with async_session() as session:
        order = await session.scalar(select(CityOrderV1).where(CityOrderV1.id == order_id))
        if not order or order.status != 'active' or order.creator_tg_id == tg_id:
            return None
        accepter = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not accepter:
            return None
        if order.role == 'passenger':
            if not accepter.is_verified:
                return None
            passenger_tg_id = order.creator_tg_id
            driver_tg_id = tg_id
        else:
            passenger_tg_id = tg_id
            driver_tg_id = order.creator_tg_id
        runtime = await session.scalar(select(CityOrderRuntime).where(CityOrderRuntime.order_id == order.id))
        existing_trip_id = runtime.active_trip_id if runtime else None
        if existing_trip_id:
            trip = await session.scalar(select(CityTripV1).where(CityTripV1.id == existing_trip_id))
            if trip:
                return trip
        trip = CityTripV1(order_id=order.id, status='accepted', price=float(order.price or 0), country=order.country, city=order.city, from_address=order.from_address, to_address=order.to_address, seats=order.seats, comment=order.comment, passenger_tg_id=passenger_tg_id, driver_tg_id=driver_tg_id, pickup_lat=(runtime.from_lat if runtime else None), pickup_lng=(runtime.from_lng if runtime else None), destination_lat=(runtime.to_lat if runtime else None), destination_lng=(runtime.to_lng if runtime else None), passenger_lat=(runtime.from_lat if runtime and order.role == 'passenger' else None), passenger_lng=(runtime.from_lng if runtime and order.role == 'passenger' else None))
        session.add(trip)
        await session.flush()
        order.accepted_by_tg_id = tg_id
        order.status = 'accepted'
        if runtime:
            runtime.active_trip_id = trip.id
        await session.commit()
        await session.refresh(trip)
        return trip


async def create_intercity_route_bot(*, creator_tg_id: int, country: str, from_city: str, to_city: str, date: str, time: str, seats: int = 1, price: float = 0.0, comment: str = '', pickup_mode: str = 'ask_driver') -> IntercityRouteV1:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == creator_tg_id))
        if not user or not user.is_verified:
            raise ValueError('Only verified drivers can create routes')
        row = IntercityRouteV1(creator_tg_id=creator_tg_id, country=country, from_city=from_city, to_city=to_city, departure_date=date, departure_time=time, seats=max(1, int(seats or 1)), price=float(price or 0), comment=comment or '', status='active')
        session.add(row)
        await session.flush()
        session.add(IntercityRouteMeta(route_id=row.id, pickup_mode=pickup_mode or 'ask_driver'))
        await session.commit()
        await session.refresh(row)
        return row


async def create_intercity_request_bot(*, creator_tg_id: int, country: str, from_city: str, to_city: str, date: str, time: str, seats_needed: int = 1, price_offer: float = 0.0, comment: str = '') -> IntercityRequestV1:
    async with async_session() as session:
        row = IntercityRequestV1(creator_tg_id=creator_tg_id, country=country, from_city=from_city, to_city=to_city, desired_date=date, desired_time=time, seats_needed=max(1, int(seats_needed or 1)), price_offer=float(price_offer or 0), comment=comment or '', status='active')
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def list_intercity_market_for_user(tg_id: int, *, kind: str, limit: int = 10) -> list[Any]:
    async with async_session() as session:
        if kind == 'route':
            rows = (await session.scalars(select(IntercityRouteV1).where(IntercityRouteV1.status == 'active').order_by(IntercityRouteV1.id.desc()).limit(limit * 2))).all()
            return [row for row in rows if row.creator_tg_id != tg_id][:limit]
        rows = (await session.scalars(select(IntercityRequestV1).where(IntercityRequestV1.status == 'active').order_by(IntercityRequestV1.id.desc()).limit(limit * 2))).all()
        return [row for row in rows if row.creator_tg_id != tg_id][:limit]


async def accept_intercity_offer_for_user(*, kind: str, item_id: int, tg_id: int):
    async with async_session() as session:
        if kind == 'route':
            row = await session.scalar(select(IntercityRouteV1).where(IntercityRouteV1.id == item_id).with_for_update())
            if not row or row.creator_tg_id == tg_id or row.status not in {'active', 'accepted'}:
                return None
            if row.accepted_by_tg_id and row.accepted_by_tg_id != tg_id:
                return None
            row.accepted_by_tg_id = tg_id
            row.status = 'accepted'
            await session.commit()
            await session.refresh(row)
            return row
        row = await session.scalar(select(IntercityRequestV1).where(IntercityRequestV1.id == item_id).with_for_update())
        if not row or row.creator_tg_id == tg_id or row.status not in {'active', 'accepted'}:
            return None
        driver = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not driver or not driver.is_verified:
            return None
        if row.accepted_by_tg_id and row.accepted_by_tg_id != tg_id:
            return None
        row.accepted_by_tg_id = tg_id
        row.status = 'accepted'
        await session.commit()
        await session.refresh(row)
        return row
