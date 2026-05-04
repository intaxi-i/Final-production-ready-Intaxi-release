from __future__ import annotations

from pydantic import BaseModel, Field


class IntercityRequestCreate(BaseModel):
    mode: str = "regular"
    country_code: str = Field(min_length=2, max_length=8)
    from_city_id: int | None = None
    to_city_id: int | None = None
    from_text: str = Field(min_length=1)
    to_text: str = Field(min_length=1)
    date: str | None = None
    time: str | None = None
    seats: int = Field(default=1, ge=1)
    passenger_price: float = Field(gt=0)
    comment: str | None = None


class IntercityRouteCreate(BaseModel):
    mode: str = "regular"
    country_code: str = Field(min_length=2, max_length=8)
    from_city_id: int | None = None
    to_city_id: int | None = None
    from_text: str = Field(min_length=1)
    to_text: str = Field(min_length=1)
    date: str | None = None
    time: str | None = None
    seats_available: int = Field(default=1, ge=1)
    price_per_seat: float = Field(gt=0)
    pickup_mode: str = "ask_driver"
    comment: str | None = None


class IntercityOfferRead(BaseModel):
    kind: str
    id: int
    mode: str
    country_code: str
    from_text: str
    to_text: str
    date: str | None = None
    time: str | None = None
    seats: int
    price: float
    currency: str
    status: str


class IntercityTripRead(BaseModel):
    id: int
    mode: str
    source_type: str
    source_id: int
    passenger_user_id: int
    driver_user_id: int
    vehicle_id: int | None = None
    final_price: float
    currency: str
    status: str

    model_config = {"from_attributes": True}


class IntercityTripStatusUpdate(BaseModel):
    status: str
