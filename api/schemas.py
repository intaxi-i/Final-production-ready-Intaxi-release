from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1)


class DevSessionRequest(BaseModel):
    tg_id: int | None = None
    full_name: str | None = None
    username: str | None = None


class VehicleInfo(BaseModel):
    brand: str | None = None
    model: str | None = None
    plate: str | None = None
    color: str | None = None
    capacity: str | None = None
    vehicle_class: str | None = None


class UserMe(BaseModel):
    tg_id: int
    full_name: str
    username: str | None = None
    language: str | None = None
    country: str | None = None
    city: str | None = None
    balance: float = 0
    commission_due: float = 0
    free_rides_left: int = 0
    active_role: str | None = None
    is_verified: bool = False
    vehicle: VehicleInfo | None = None


class SessionResponse(BaseModel):
    session_token: str
    user: UserMe


class WalletResponse(BaseModel):
    balance: float
    commission_due: float
    free_rides_left: int
    commission_rate: float = 0


class UpdateProfileRequest(BaseModel):
    language: str | None = None
    country: str | None = None
    city: str | None = None


class UpdateRoleRequest(BaseModel):
    active_role: str


class UpdateVehicleRequest(VehicleInfo):
    pass


class UserEnvelope(BaseModel):
    user: UserMe


class SessionData(BaseModel):
    tg_id: int
    full_name: str
    username: str | None = None
    created_at: datetime


class TariffItem(BaseModel):
    country: str
    currency: str
    price_per_km: float


class TariffListResponse(BaseModel):
    items: list[TariffItem]


class TariffUpdateRequest(BaseModel):
    country: str
    price_per_km: float
    currency: str | None = None


class DriverOnlineStateResponse(BaseModel):
    is_online: bool
    lat: float | None = None
    lng: float | None = None
    updated_at: str | None = None


class DriverOnlineUpdateRequest(BaseModel):
    is_online: bool


class DriverLocationUpdateRequest(BaseModel):
    trip_id: int | None = None
    lat: float
    lng: float


class CityOrderCreateRequest(BaseModel):
    role: str
    country: str
    city: str
    from_address: str
    to_address: str
    seats: int = 1
    price: float | None = None
    comment: str = ''
    recommended_price: float | None = None
    from_lat: float | None = None
    from_lng: float | None = None
    to_lat: float | None = None
    to_lng: float | None = None


class CityOrderCreateResponse(BaseModel):
    id: int
    status: str
    recommended_price: float | None = None
    seen_by_drivers: int = 0
    currency: str | None = None
    tariff_hint: str | None = None


class RaisePriceRequest(BaseModel):
    price: float


class CityOrderResponse(BaseModel):
    id: int
    creator_tg_id: int | None = None
    creator_name: str | None = None
    creator_rating: float | None = None
    role: str
    country: str | None = None
    city: str
    from_address: str
    to_address: str | None = None
    seats: int
    price: float
    recommended_price: float | None = None
    seen_by_drivers: int | None = None
    can_raise_price_after: int | None = None
    estimated_distance_km: float | None = None
    estimated_trip_min: int | None = None
    driver_distance_km: float | None = None
    driver_eta_min: int | None = None
    comment: str | None = None
    status: str | None = None
    created_at: str | None = None
    is_mine: bool | None = None
    active_trip_id: int | None = None
    vehicle: VehicleInfo | None = None
    currency: str | None = None
    tariff_hint: str | None = None


class CityOrderListResponse(BaseModel):
    items: list[CityOrderResponse]


class CityOrderEnvelope(BaseModel):
    item: CityOrderResponse


class CityAcceptResponse(BaseModel):
    trip_id: int
    status: str


class CityTripResponse(BaseModel):
    id: int
    order_id: int
    status: str
    price: float
    country: str | None = None
    city: str | None = None
    from_address: str | None = None
    to_address: str | None = None
    seats: int | None = None
    comment: str | None = None
    passenger_tg_id: int
    driver_tg_id: int
    passenger_name: str | None = None
    passenger_username: str | None = None
    driver_name: str | None = None
    driver_username: str | None = None
    driver_rating: float | None = None
    vehicle: VehicleInfo | None = None
    trip_type: str | None = None
    pickup_lat: float | None = None
    pickup_lng: float | None = None
    destination_lat: float | None = None
    destination_lng: float | None = None
    driver_lat: float | None = None
    driver_lng: float | None = None
    passenger_lat: float | None = None
    passenger_lng: float | None = None
    map_provider: str | None = None
    map_embed_url: str | None = None
    map_action_url: str | None = None
    eta_min: int | None = None


class CityTripEnvelope(BaseModel):
    item: CityTripResponse


class CityTripStatusUpdateRequest(BaseModel):
    status: str


class CurrentTripResponse(BaseModel):
    item: dict | None = None


class ChatMessageRequest(BaseModel):
    text: str


class ChatMessageResponse(BaseModel):
    id: int
    sender_tg_id: int
    text: str
    created_at: str


class ChatMessageListResponse(BaseModel):
    items: list[ChatMessageResponse]


class ChatCreatedResponse(BaseModel):
    id: int
    status: str


class PaymentRequestCreate(BaseModel):
    amount: float
    card_country: str | None = None
    receipt_file_id: str | None = None


class PaymentItem(BaseModel):
    id: int
    amount: float
    status: str
    card_country: str | None = None
    admin_card_number: str | None = None
    receipt_file_id: str | None = None
    reviewed_by: int | None = None
    created_at: str | None = None
    reviewed_at: str | None = None
    driver_tg_id: int | None = None
    driver_balance: float | None = None


class PaymentListResponse(BaseModel):
    items: list[PaymentItem]


class PaymentReviewResponse(BaseModel):
    id: int
    status: str
    driver_tg_id: int | None = None
    amount: float | None = None
    reviewed_by: int | None = None
    reviewed_at: str | None = None
    driver_balance: float | None = None


class PaymentApproveRequest(BaseModel):
    amount: float | None = None


class IntercityRouteCreateRequest(BaseModel):
    country: str
    from_city: str
    to_city: str
    date: str
    time: str
    seats: int
    price: float
    comment: str = ''
    pickup_mode: str | None = 'ask_driver'


class IntercityRequestCreateRequest(BaseModel):
    country: str
    from_city: str
    to_city: str
    date: str
    time: str
    seats_needed: int
    price_offer: float
    comment: str = ''


class IntercityOfferResponse(BaseModel):
    kind: str
    id: int
    creator_tg_id: int | None = None
    creator_name: str | None = None
    country: str | None = None
    from_city: str
    to_city: str
    date: str
    time: str
    seats: int
    price: float
    comment: str | None = None
    status: str | None = None
    created_at: str | None = None
    is_mine: bool | None = None
    pickup_mode: str | None = None
    active_trip_id: int | None = None
    accepted_by_tg_id: int | None = None
    can_accept: bool | None = None
    map_provider: str | None = None
    map_embed_url: str | None = None
    map_action_url: str | None = None


class IntercityOfferListResponse(BaseModel):
    items: list[IntercityOfferResponse]


class IntercityOfferEnvelope(BaseModel):
    item: IntercityOfferResponse


class IntercityOwnRouteResponse(BaseModel):
    id: int
    country: str | None = None
    from_city: str
    to_city: str
    date: str
    time: str
    seats: int
    price: float
    comment: str | None = None
    status: str | None = None
    created_at: str | None = None
    pickup_mode: str | None = None


class IntercityOwnRequestResponse(BaseModel):
    id: int
    country: str | None = None
    from_city: str
    to_city: str
    date: str
    time: str
    seats_needed: int
    price_offer: float
    comment: str | None = None
    status: str | None = None
    created_at: str | None = None


class IntercityOwnRouteListResponse(BaseModel):
    items: list[IntercityOwnRouteResponse]


class IntercityOwnRequestListResponse(BaseModel):
    items: list[IntercityOwnRequestResponse]


class IntercityStatusUpdateRequest(BaseModel):
    status: str


class IntercityAcceptResponse(BaseModel):
    trip_id: int
    trip_type: str
    status: str


class HistoryResponse(BaseModel):
    city_orders: list[CityOrderResponse]
    city_trips: list[CityTripResponse]
    intercity_routes: list[IntercityOwnRouteResponse]
    intercity_requests: list[IntercityOwnRequestResponse]
