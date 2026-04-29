# Intaxi V2 Data Model

This is the target data model for the clean V2 rebuild.

## 1. General rules

- PostgreSQL is the production database.
- SQLAlchemy async is the ORM.
- Alembic owns migrations.
- All money mutations must use ledger records.
- All admin decisions must have audit fields.
- Business status values must be centralized.

## 2. Users

### users

```text
id: bigint pk
tg_id: bigint unique nullable
phone: varchar nullable unique
full_name: varchar not null
username: varchar nullable
language: varchar default 'ru'
country_code: varchar nullable
city_id: bigint nullable
active_role: enum(passenger, driver, admin) nullable
is_blocked: bool default false
block_reason: text nullable
gender: enum(female, male, unspecified) default unspecified
is_adult_confirmed: bool default false
rating: numeric default 0
rating_count: int default 0
created_at: timestamp
updated_at: timestamp
last_seen_at: timestamp nullable
```

## 3. Driver verification

### driver_profiles

```text
id: bigint pk
user_id: bigint fk users unique
status: enum(not_started, pending, approved, rejected, suspended)
country_code: varchar not null
city_id: bigint nullable
license_number: varchar nullable
license_photo_file_id: varchar nullable
identity_photo_file_id: varchar nullable
selfie_file_id: varchar nullable
is_woman_driver_verified: bool default false
woman_driver_status: enum(not_requested, pending, approved, rejected) default not_requested
adult_confirmed_at: timestamp nullable
submitted_at: timestamp nullable
reviewed_by_admin_id: bigint nullable
reviewed_at: timestamp nullable
rejection_reason: text nullable
created_at: timestamp
updated_at: timestamp
```

## 4. Vehicles

### vehicles

```text
id: bigint pk
driver_user_id: bigint fk users
country_code: varchar not null
brand: varchar not null
model: varchar not null
year: int nullable
color: varchar nullable
plate: varchar not null
capacity: int default 4
vehicle_class: enum(economy, comfort, business, minivan, cargo) default economy
photo_front_file_id: varchar nullable
photo_back_file_id: varchar nullable
photo_inside_file_id: varchar nullable
tech_passport_file_id: varchar nullable
status: enum(pending, approved, rejected, disabled) default pending
reviewed_by_admin_id: bigint nullable
reviewed_at: timestamp nullable
rejection_reason: text nullable
created_at: timestamp
updated_at: timestamp
```

## 5. Driver payment details

### driver_payment_methods

```text
id: bigint pk
driver_user_id: bigint fk users
country_code: varchar not null
method_type: enum(card, cash, bank_transfer, other)
card_number_masked: varchar nullable
card_number_encrypted: text nullable
card_holder_name: varchar nullable
bank_name: varchar nullable
is_active: bool default true
created_at: timestamp
updated_at: timestamp
```

Visibility rule: passenger can view active driver payment details only when passenger is assigned to an active or just-completed trip with that driver.

## 6. Driver online state

### driver_online_states

```text
driver_user_id: bigint pk fk users
is_online: bool default false
is_busy: bool default false
country_code: varchar nullable
city_id: bigint nullable
lat: numeric nullable
lng: numeric nullable
last_location_at: timestamp nullable
shift_started_at: timestamp nullable
shift_minutes_today: int default 0
updated_at: timestamp
```

## 7. Countries and cities

### countries

```text
code: varchar pk
name_en: varchar
name_ru: varchar
name_local: varchar
currency: varchar
is_active: bool default true
map_provider: enum(yandex, google, osm, mixed)
default_language: varchar
created_at: timestamp
updated_at: timestamp
```

### cities

```text
id: bigint pk
country_code: varchar fk countries
region_name: varchar nullable
name_en: varchar
name_ru: varchar
name_local: varchar
lat: numeric nullable
lng: numeric nullable
is_active: bool default true
created_at: timestamp
updated_at: timestamp
```

## 8. Commission settings

### commission_rules

```text
id: bigint pk
scope_type: enum(global, country, city, driver)
scope_id: varchar not null
commission_percent: numeric default 0
free_first_rides: int default 0
starts_at: timestamp nullable
ends_at: timestamp nullable
is_active: bool default true
created_by_admin_id: bigint nullable
updated_by_admin_id: bigint nullable
created_at: timestamp
updated_at: timestamp
```

Resolution order:

1. active driver rule;
2. active city rule;
3. active country rule;
4. active global rule;
5. fallback 0%.

## 9. City orders

### city_orders

```text
id: bigint pk
mode: enum(regular, women) default regular
passenger_user_id: bigint fk users
country_code: varchar not null
city_id: bigint nullable
pickup_address: text not null
pickup_lat: numeric nullable
pickup_lng: numeric nullable
destination_address: text not null
destination_lat: numeric nullable
destination_lng: numeric nullable
seats: int default 1
passenger_price: numeric not null
recommended_price: numeric nullable
minimum_recommended_price: numeric nullable
currency: varchar not null
estimated_distance_km: numeric nullable
estimated_duration_min: int nullable
status: enum(draft, active, accepted, in_progress, completed, cancelled, expired, disputed) default active
seen_by_drivers: int default 0
accepted_trip_id: bigint nullable
cancel_reason: text nullable
created_at: timestamp
updated_at: timestamp
expires_at: timestamp nullable
```

## 10. Driver counteroffers

### city_counteroffers

```text
id: bigint pk
order_id: bigint fk city_orders
driver_user_id: bigint fk users
price: numeric not null
currency: varchar not null
eta_min: int nullable
distance_to_pickup_km: numeric nullable
status: enum(pending, accepted, rejected, expired, cancelled) default pending
created_at: timestamp
updated_at: timestamp
expires_at: timestamp nullable
```

## 11. City trips

### city_trips

```text
id: bigint pk
mode: enum(regular, women) default regular
order_id: bigint fk city_orders unique
passenger_user_id: bigint fk users
driver_user_id: bigint fk users
vehicle_id: bigint fk vehicles nullable
final_price: numeric not null
currency: varchar not null
status: enum(accepted, driver_on_way, driver_arrived, in_progress, completed, cancelled, disputed) default accepted
pickup_address: text
pickup_lat: numeric nullable
pickup_lng: numeric nullable
destination_address: text
destination_lat: numeric nullable
destination_lng: numeric nullable
driver_lat: numeric nullable
driver_lng: numeric nullable
passenger_lat: numeric nullable
passenger_lng: numeric nullable
accepted_at: timestamp
started_at: timestamp nullable
completed_at: timestamp nullable
cancelled_at: timestamp nullable
cancel_reason: text nullable
created_at: timestamp
updated_at: timestamp
```

## 12. Intercity

### intercity_requests

Passenger-created request.

```text
id: bigint pk
mode: enum(regular, women) default regular
passenger_user_id: bigint fk users
country_code: varchar not null
from_city_id: bigint nullable
to_city_id: bigint nullable
from_text: varchar not null
to_text: varchar not null
date: date nullable
time: varchar nullable
seats: int default 1
passenger_price: numeric not null
recommended_price: numeric nullable
currency: varchar not null
status: enum(active, accepted, in_progress, completed, cancelled, expired, disputed)
created_at: timestamp
updated_at: timestamp
```

### intercity_routes

Driver-created route.

```text
id: bigint pk
mode: enum(regular, women) default regular
driver_user_id: bigint fk users
country_code: varchar not null
from_city_id: bigint nullable
to_city_id: bigint nullable
from_text: varchar not null
to_text: varchar not null
date: date nullable
time: varchar nullable
seats_available: int default 1
price_per_seat: numeric not null
currency: varchar not null
pickup_mode: enum(fixed_point, ask_driver, door_to_door) default ask_driver
status: enum(active, accepted, in_progress, completed, cancelled, expired, disputed)
created_at: timestamp
updated_at: timestamp
```

### intercity_trips

Accepted intercity request or route.

```text
id: bigint pk
mode: enum(regular, women) default regular
source_type: enum(request, route)
source_id: bigint not null
passenger_user_id: bigint fk users
driver_user_id: bigint fk users
vehicle_id: bigint fk vehicles nullable
final_price: numeric not null
currency: varchar not null
status: enum(accepted, driver_on_way, in_progress, completed, cancelled, disputed)
created_at: timestamp
updated_at: timestamp
```

## 13. Wallet and ledger

### wallets

```text
user_id: bigint pk fk users
balance: numeric default 0
hold_balance: numeric default 0
currency: varchar nullable
updated_at: timestamp
```

### wallet_ledger_entries

```text
id: bigint pk
user_id: bigint fk users
wallet_id: bigint nullable
entry_type: enum(topup, commission, adjustment, refund, hold, release)
amount: numeric not null
currency: varchar not null
direction: enum(credit, debit)
related_type: varchar nullable
related_id: bigint nullable
balance_before: numeric not null
balance_after: numeric not null
created_by_user_id: bigint nullable
created_by_admin_id: bigint nullable
comment: text nullable
created_at: timestamp
```

## 14. Payment topups

### payment_topup_requests

```text
id: bigint pk
driver_user_id: bigint fk users
amount: numeric not null
currency: varchar not null
method: enum(card_transfer, cash, bank_transfer, other)
receipt_file_id: varchar nullable
status: enum(pending, approved, rejected, cancelled)
reviewed_by_admin_id: bigint nullable
reviewed_at: timestamp nullable
rejection_reason: text nullable
created_at: timestamp
updated_at: timestamp
```

## 15. Ratings

### ratings

```text
id: bigint pk
trip_type: enum(city, intercity)
trip_id: bigint not null
from_user_id: bigint fk users
to_user_id: bigint fk users
stars: int not null
reason: varchar nullable
comment: text nullable
created_at: timestamp
```

## 16. Support

### support_tickets

```text
id: bigint pk
created_by_user_id: bigint fk users
assigned_admin_id: bigint nullable
related_type: varchar nullable
related_id: bigint nullable
ticket_type: enum(general, payment, safety, complaint, accident, lost_item, cancellation, technical)
priority: enum(low, normal, high, urgent)
status: enum(open, in_review, waiting_user, resolved, rejected, closed)
subject: varchar nullable
message: text not null
admin_notes: text nullable
created_at: timestamp
updated_at: timestamp
closed_at: timestamp nullable
```

## 17. Admin audit log

### admin_audit_logs

```text
id: bigint pk
admin_user_id: bigint fk users
action: varchar not null
entity_type: varchar not null
entity_id: varchar not null
before_json: jsonb nullable
after_json: jsonb nullable
ip_address: varchar nullable
created_at: timestamp
```

## 18. Domain events

### domain_events

```text
id: bigint pk
event_type: varchar not null
entity_type: varchar not null
entity_id: varchar not null
payload_json: jsonb not null
processed_at: timestamp nullable
created_at: timestamp
```
