from __future__ import annotations

from pydantic import BaseModel, Field


class CityOrderCreate(BaseModel):
    mode: str = "regular"
    country_code: str = Field(min_length=2, max_length=8)
    city_id: int | None = None
    pickup_address: str = Field(min_length=1)
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    destination_address: str = Field(min_length=1)
    destination_lat: float | None = None
    destination_lng: float | None = None
    seats: int = Field(default=1, ge=1)
    passenger_price: float = Field(gt=0)
    comment: str | None = None


class CityOrderRead(BaseModel):
    id: int
    mode: str
    passenger_user_id: int
    country_code: str
    city_id: int | None
    pickup_address: str
    destination_address: str
    seats: int
    passenger_price: float
    recommended_price: float | None = None
    minimum_recommended_price: float | None = None
    currency: str
    estimated_distance_km: float | None = None
    estimated_duration_min: int | None = None
    status: str
    seen_by_drivers: int
    accepted_trip_id: int | None = None
    comment: str | None = None

    model_config = {"from_attributes": True}


class CityOrderCreateResponse(BaseModel):
    order: CityOrderRead
    recommended_price: float | None = None
    minimum_recommended_price: float | None = None
    seen_by_drivers: int = 0


class RaisePriceRequest(BaseModel):
    price: float = Field(gt=0)


class CounterofferCreate(BaseModel):
    price: float = Field(gt=0)


class CounterofferRead(BaseModel):
    id: int
    order_id: int
    driver_user_id: int
    price: float
    currency: str
    eta_min: int | None = None
    distance_to_pickup_km: float | None = None
    status: str

    model_config = {"from_attributes": True}


class CityTripRead(BaseModel):
    id: int
    mode: str
    order_id: int
    passenger_user_id: int
    driver_user_id: int
    vehicle_id: int | None = None
    final_price: float
    currency: str
    status: str
    pickup_address: str
    destination_address: str
    driver_lat: float | None = None
    driver_lng: float | None = None

    model_config = {"from_attributes": True}


class CityTripStatusUpdate(BaseModel):
    status: str


class CurrentTripResponse(BaseModel):
    item: CityTripRead | None = None
