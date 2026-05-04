# Intaxi V2 Architecture Plan

## 1. Target repository layout

Preferred final layout:

```text
/backend
  app/
    main.py
    core/
      config.py
      security.py
      database.py
      errors.py
      logging.py
    domain/
      statuses.py
      entities.py
      events.py
    models/
      user.py
      driver.py
      vehicle.py
      city_order.py
      city_trip.py
      wallet.py
      rating.py
      support.py
      admin.py
      country.py
    schemas/
      auth.py
      user.py
      city.py
      driver.py
      wallet.py
      admin.py
      support.py
    services/
      auth_service.py
      pricing_service.py
      city_order_service.py
      city_trip_service.py
      driver_availability_service.py
      wallet_service.py
      rating_service.py
      support_service.py
      notification_service.py
      country_service.py
    repositories/
      users.py
      drivers.py
      city_orders.py
      city_trips.py
      wallets.py
      ratings.py
      support.py
    api/
      v1/
        auth.py
        me.py
        city.py
        driver.py
        wallet.py
        admin.py
        support.py
    integrations/
      telegram.py
      maps.py
      storage.py
    tests/
      test_city_flow.py
      test_driver_availability.py
      test_wallet_ledger.py

/bot
  app/
    main.py
    handlers/
    keyboards/
    presenters/
    api_client.py
    notifications.py

/miniapp
  app/
  components/
  lib/
  flows/

/admin
  app/
  components/
  lib/

/shared
  status_contract.json
  country_config.json
  api_contract.md
```

Current repo may keep its existing folders during migration, but V2 logic must follow this separation.

## 2. Backend principles

The backend owns business rules.

Do not place business rules directly in:

- React pages;
- Telegram handlers;
- one-off hotfix modules;
- runtime monkey patches.

Telegram bot and Mini App must call backend endpoints or shared service functions.

## 3. Service boundaries

### CityOrderService

Owns:

- create order;
- validate passenger role;
- calculate recommended price;
- publish order to eligible drivers;
- raise passenger price;
- expire order;
- cancel order.

### DriverAvailabilityService

Owns:

- online/offline state;
- driver live location;
- eligibility rules;
- busy/free state;
- matching drivers to order;
- excluding active-trip drivers.

### CityTripService

Owns:

- accept order;
- create trip;
- status transitions;
- current trip lookup;
- finish/cancel trip;
- sync order status;
- trigger rating/finance events.

### PricingService

Owns:

- country tariff;
- recommended price;
- minimum reasonable price;
- distance/ETA wrapper;
- currency display metadata.

### WalletService

Owns:

- driver balance;
- commission;
- topup request;
- admin approval;
- ledger entries;
- manual adjustments.

### NotificationService

Owns:

- Telegram notifications;
- Mini App event payloads;
- status update messages;
- safety/support notifications.

### SupportService

Owns:

- tickets;
- complaints;
- trip-linked support;
- admin review status.

## 4. API contract first

Every user action must have an API contract before UI implementation.

City endpoints:

```text
POST   /api/v1/city/orders
GET    /api/v1/city/orders/my
GET    /api/v1/city/orders/available
GET    /api/v1/city/orders/{order_id}
POST   /api/v1/city/orders/{order_id}/raise-price
POST   /api/v1/city/orders/{order_id}/cancel
POST   /api/v1/city/orders/{order_id}/accept
POST   /api/v1/city/orders/{order_id}/counteroffers
POST   /api/v1/city/counteroffers/{offer_id}/accept
GET    /api/v1/city/trips/current
GET    /api/v1/city/trips/{trip_id}
POST   /api/v1/city/trips/{trip_id}/status
POST   /api/v1/city/trips/{trip_id}/cancel
POST   /api/v1/city/trips/{trip_id}/rating
```

Driver endpoints:

```text
GET    /api/v1/driver/profile
POST   /api/v1/driver/profile
GET    /api/v1/driver/online
POST   /api/v1/driver/online
POST   /api/v1/driver/location
GET    /api/v1/driver/orders/available
GET    /api/v1/driver/history
```

Wallet endpoints:

```text
GET    /api/v1/wallet
GET    /api/v1/wallet/ledger
POST   /api/v1/wallet/topups
GET    /api/v1/wallet/topups
```

Admin endpoints:

```text
GET    /api/v1/admin/drivers/pending
POST   /api/v1/admin/drivers/{driver_id}/approve
POST   /api/v1/admin/drivers/{driver_id}/reject
GET    /api/v1/admin/orders
GET    /api/v1/admin/trips
GET    /api/v1/admin/payments/pending
POST   /api/v1/admin/payments/{payment_id}/approve
POST   /api/v1/admin/payments/{payment_id}/reject
GET    /api/v1/admin/support/tickets
POST   /api/v1/admin/support/tickets/{ticket_id}/resolve
GET    /api/v1/admin/countries
POST   /api/v1/admin/countries/{country_code}/tariffs
```

## 5. Event model

Important actions should emit domain events internally:

- city_order_created;
- driver_counteroffer_created;
- city_order_accepted;
- city_trip_status_changed;
- city_trip_completed;
- city_trip_cancelled;
- payment_topup_requested;
- payment_topup_approved;
- support_ticket_created;
- rating_created.

Events feed notifications, audit log, history and analytics.

## 6. Migration strategy

Phase 0: freeze current hotfix growth.

Phase 1: add V2 docs and contracts.

Phase 2: build V2 backend services in parallel modules.

Phase 3: add tests/smoke scripts for V2 city flow.

Phase 4: connect Mini App city screens to V2 endpoints.

Phase 5: connect Telegram bot to V2 API/client instead of direct DB/hotfix logic.

Phase 6: remove runtime patches and old duplicate logic.

Phase 7: migrate intercity, wallet, admin and support.

## 7. Rewrite policy

Old code may be reused only if:

- it matches V2 contracts;
- it does not duplicate business rules;
- it is testable;
- it has clear ownership;
- it does not require monkey patching.

Otherwise rewrite cleanly.

## 8. Testing requirements

Minimum tests before release:

- passenger can create city order;
- unavailable driver cannot see/accept order;
- available driver can accept order;
- passenger cannot update trip status;
- unrelated driver cannot update trip status;
- assigned driver can update valid statuses;
- invalid status transition is rejected;
- completed trip updates order status;
- driver with active trip cannot accept another order;
- wallet ledger records commission mutation.

## 9. Deployment requirements

Production must have:

- separate env config;
- no dev session in production;
- database migrations;
- structured logs;
- error monitoring;
- backup plan;
- healthcheck endpoint;
- deployment rollback path;
- no secrets committed to repo.
