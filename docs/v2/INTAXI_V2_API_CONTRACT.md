# Intaxi V2 API Contract

Base path: `/api/v2`

All endpoints return structured errors:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

## 1. Auth and session

### POST /auth/telegram

Validates Telegram WebApp init data and creates session.

Request:

```json
{
  "init_data": "string"
}
```

Response:

```json
{
  "session_token": "string",
  "user": "UserMe"
}
```

### GET /me

Returns current user profile.

### PATCH /me

Updates language, country, city, gender, adult confirmation and profile basics.

### POST /me/role

Switch active role.

Rules:

- passenger role is open for all non-blocked users;
- driver role requires approved driver profile;
- admin role requires admin permission.

## 2. Countries and config

### GET /countries

Returns active countries, cities, currencies, map providers and enabled features.

### GET /countries/{country_code}/config

Returns country-specific config.

## 3. Driver profile

### GET /driver/profile

Returns driver profile, vehicle, verification state and payment methods.

### POST /driver/profile

Creates or updates driver profile.

### POST /driver/vehicle

Creates or updates vehicle data.

### POST /driver/payment-methods

Creates driver payment details.

### GET /driver/payment-methods

Driver sees own payment methods.

### GET /driver/online

Returns online state.

### POST /driver/online

Request:

```json
{
  "is_online": true,
  "city_id": 1,
  "country_code": "uz"
}
```

Rules:

- only approved drivers can go online;
- blocked drivers cannot go online;
- if active trip exists, driver remains busy.

### POST /driver/location

Updates live location.

Request:

```json
{
  "lat": 41.3111,
  "lng": 69.2797,
  "trip_id": 123
}
```

## 4. City orders

### POST /city/orders

Creates city order.

Request:

```json
{
  "mode": "regular",
  "country_code": "uz",
  "city_id": 1,
  "pickup_address": "string",
  "pickup_lat": 41.3111,
  "pickup_lng": 69.2797,
  "destination_address": "string",
  "destination_lat": 41.3200,
  "destination_lng": 69.3000,
  "seats": 1,
  "passenger_price": 30000,
  "comment": "string"
}
```

Rules:

- active role must be passenger;
- women mode requires eligible female passenger profile;
- passenger_price must be positive;
- destination is required;
- backend calculates recommended price if coordinates exist;
- order status becomes active;
- matching drivers are computed from DriverAvailabilityService.

Response:

```json
{
  "order": "CityOrder",
  "recommended_price": 32000,
  "minimum_recommended_price": 25000,
  "seen_by_drivers": 3
}
```

### GET /city/orders/my

Passenger sees own city orders.

### GET /city/orders/available

Driver sees available matching orders.

Rules:

- only approved online drivers;
- active_role must be driver;
- no active trip;
- matching country/city;
- women mode requires approved woman driver.

### GET /city/orders/{order_id}

Returns order details if requester has access.

### POST /city/orders/{order_id}/raise-price

Passenger raises own active order price.

### POST /city/orders/{order_id}/cancel

Cancels active order or active trip if allowed.

### POST /city/orders/{order_id}/accept

Driver accepts passenger price.

Rules:

- only eligible driver;
- order must be active;
- order must not already have accepted trip;
- creates CityTrip;
- order status becomes accepted;
- trip status becomes accepted;
- driver becomes busy;
- domain event `city_order_accepted` is emitted.

### POST /city/orders/{order_id}/counteroffers

Driver sends own price.

Request:

```json
{
  "price": 35000
}
```

Rules:

- only eligible driver;
- order must be active;
- one active counteroffer per driver/order unless replaced.

### POST /city/counteroffers/{offer_id}/accept

Passenger accepts driver counteroffer.

Rules:

- only order owner;
- offer must be pending;
- creates CityTrip;
- final price is offer price;
- all other offers become rejected/expired.

## 5. City trips

### GET /city/trips/current

Returns active trip for current user.

### GET /city/trips/{trip_id}

Returns trip details if user is participant or admin.

### POST /city/trips/{trip_id}/status

Driver updates trip status.

Request:

```json
{
  "status": "driver_on_way"
}
```

Rules:

- only assigned driver;
- valid transition only;
- passenger cannot update status;
- order status is synchronized;
- completed trip triggers finance/rating/history events.

### GET /city/trips/{trip_id}/driver-payment-methods

Passenger sees assigned driver's active payment details.

Rules:

- only passenger of the trip;
- trip must be active or recently completed;
- details must not be public.

### POST /city/trips/{trip_id}/rating

Creates post-trip rating.

## 6. Intercity

### POST /intercity/requests

Passenger creates intercity request.

### POST /intercity/routes

Driver creates intercity route.

### GET /intercity/offers

Returns matching intercity requests/routes.

### POST /intercity/offers/{kind}/{id}/accept

Accepts intercity request/route and creates intercity trip.

### GET /intercity/trips/current

Returns active intercity trip.

### POST /intercity/trips/{trip_id}/status

Updates intercity trip status.

Women mode rules mirror city mode.

## 7. Wallet

### GET /wallet

Returns wallet summary.

### GET /wallet/ledger

Returns ledger entries.

### POST /wallet/topups

Driver creates topup request.

### GET /wallet/topups

Driver sees own topup requests.

## 8. Support

### POST /support/tickets

Creates ticket.

Request may include related trip/order id.

### GET /support/tickets

User sees own tickets.

### POST /support/tickets/{ticket_id}/messages

Adds ticket message.

## 9. Admin

All admin endpoints require admin permission.

### GET /admin/dashboard

Returns counts and critical states.

### GET /admin/drivers/pending

Returns pending driver profiles and vehicles.

### POST /admin/drivers/{driver_profile_id}/approve

Approves driver.

### POST /admin/drivers/{driver_profile_id}/reject

Rejects driver with reason.

### POST /admin/drivers/{driver_profile_id}/approve-woman-mode

Approves woman driver eligibility.

### GET /admin/orders

Filters city/intercity orders.

### GET /admin/trips

Filters city/intercity trips.

### GET /admin/payments/pending

Returns pending topups.

### POST /admin/payments/{payment_id}/approve

Approves topup and writes wallet ledger.

### POST /admin/payments/{payment_id}/reject

Rejects topup.

### GET /admin/commission-rules

Returns commission rules.

### POST /admin/commission-rules

Creates commission rule.

### PATCH /admin/commission-rules/{rule_id}

Updates commission rule.

### POST /admin/wallets/{user_id}/adjust

Manual adjustment with audit log.

### GET /admin/support/tickets

Returns support queue.

### POST /admin/support/tickets/{ticket_id}/resolve

Resolves ticket.

## 10. Bot usage of API

Bot must use API/client layer for:

- current trip link;
- fast actions;
- driver accept;
- counteroffer;
- status update;
- admin approvals.

Bot must not directly duplicate pricing, matching, wallet or status transition logic.
