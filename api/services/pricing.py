from __future__ import annotations

from math import ceil

from sqlalchemy import select

from intaxi_bot.app.database.models import TariffSetting, async_session
from intaxi_bot.app.database.requests import DEFAULT_TARIFFS, haversine_km


async def get_tariff(country: str | None) -> TariffSetting:
    country_key = (country or 'uz').lower()
    async with async_session() as session:
        row = await session.scalar(select(TariffSetting).where(TariffSetting.country == country_key))
        if row:
            return row
        currency, price = DEFAULT_TARIFFS.get(country_key, ('USD', 1.0))
        row = TariffSetting(country=country_key, currency=currency, price_per_km=price)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def currency_hint(country: str | None) -> tuple[str, str]:
    tariff = await get_tariff(country)
    return tariff.currency, f'~{tariff.price_per_km:g} {tariff.currency}/km'


async def recommended_price(
    country: str | None,
    from_lat: float | None,
    from_lng: float | None,
    to_lat: float | None,
    to_lng: float | None,
) -> tuple[float | None, float | None, int | None, str | None, str | None]:
    currency, hint = await currency_hint(country)
    if None in (from_lat, from_lng, to_lat, to_lng):
        return None, None, None, currency, hint
    distance = haversine_km(float(from_lat), float(from_lng), float(to_lat), float(to_lng))
    tariff = await get_tariff(country)
    price = round(distance * float(tariff.price_per_km), 2)
    eta = max(3, ceil(distance / 0.45))
    return price, round(distance, 2), eta, tariff.currency, hint
