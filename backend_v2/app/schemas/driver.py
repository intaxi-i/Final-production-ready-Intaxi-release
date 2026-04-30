from __future__ import annotations

from pydantic import BaseModel, Field


class DriverProfileCreate(BaseModel):
    country_code: str = Field(min_length=2, max_length=8)
    city_id: int | None = None
    license_number: str | None = None
    license_photo_file_id: str | None = None
    identity_photo_file_id: str | None = None
    selfie_file_id: str | None = None
    request_woman_mode: bool = False


class DriverProfileRead(BaseModel):
    id: int
    user_id: int
    status: str
    country_code: str
    city_id: int | None = None
    license_number: str | None = None
    license_photo_file_id: str | None = None
    identity_photo_file_id: str | None = None
    selfie_file_id: str | None = None
    is_woman_driver_verified: bool
    woman_driver_status: str
    rejection_reason: str | None = None

    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    country_code: str = Field(min_length=2, max_length=8)
    brand: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    year: int | None = None
    color: str | None = None
    plate: str = Field(min_length=1, max_length=64)
    capacity: int = Field(default=4, ge=1, le=12)
    vehicle_class: str = "economy"
    photo_front_file_id: str | None = None
    photo_back_file_id: str | None = None
    photo_inside_file_id: str | None = None
    tech_passport_file_id: str | None = None


class VehicleRead(BaseModel):
    id: int
    driver_user_id: int
    country_code: str
    brand: str
    model: str
    year: int | None = None
    color: str | None = None
    plate: str
    capacity: int
    vehicle_class: str
    status: str
    rejection_reason: str | None = None

    model_config = {"from_attributes": True}


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
