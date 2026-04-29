from __future__ import annotations

from pydantic import BaseModel, Field


class DriverOnlineRead(BaseModel):
    is_online: bool
    is_busy: bool = False
    country_code: str | None = None
    city_id: int | None = None
    lat: float | None = None
    lng: float | None = None


class DriverOnlineUpdate(BaseModel):
    is_online: bool
    country_code: str | None = None
    city_id: int | None = None


class DriverLocationUpdate(BaseModel):
    lat: float
    lng: float
    trip_id: int | None = None


class DriverPaymentMethodCreate(BaseModel):
    country_code: str = Field(min_length=2, max_length=8)
    method_type: str = "card"
    card_number: str | None = None
    card_holder_name: str | None = None
    bank_name: str | None = None


class DriverPaymentMethodRead(BaseModel):
    id: int
    method_type: str
    card_number_masked: str | None = None
    card_holder_name: str | None = None
    bank_name: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}
