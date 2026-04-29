# Intaxi V2 Master Specification

## 1. Product goal

Intaxi V2 is a full taxi marketplace, not just a Telegram bot. Telegram bot, Mini App, API, database, admin tools, finance, safety, support, notifications and history must behave as one product.

Core positioning:

- passenger and driver can agree on price;
- Intaxi keeps low transparent commission;
- city and intercity flows are supported;
- safety, verification, support and ratings are first-class features;
- Uzbekistan, Turkey, Saudi Arabia and Kazakhstan are supported through country config, not hardcoded branches.

## 2. Non-negotiable architecture rule

DB is the source of truth.
API owns all business logic.
Mini App is the main user interface.
Telegram bot is fast access, notifications and fallback interface.
Admin controls moderation, finance, safety and support.

No business flow may be implemented separately in bot and Mini App. Bot and Mini App must call the same API/service logic or use the same backend service functions.

## 3. Primary roles

### Passenger

Can:

- create city order;
- choose pickup and destination by address or map point;
- see recommended price, distance, ETA and currency;
- offer own price;
- receive driver offers;
- choose driver based on price, ETA, rating, vehicle and verification;
- see current trip;
- contact driver through safe channel;
- share trip;
- open support/safety tools;
- rate driver;
- view history.

### Driver

Can:

- register as driver;
- upload required documents and vehicle data;
- wait for admin verification;
- switch online/offline;
- provide live location;
- see matching passenger orders;
- accept passenger price;
- send counteroffer;
- run trip statuses;
- view balance and history;
- top up balance if required;
- contact support;
- rate passenger.

### Admin

Can:

- moderate drivers;
- approve/reject documents;
- inspect active/completed/cancelled/disputed orders;
- approve/reject payments;
- adjust balances with audit trail;
- manage countries, cities, tariffs, commissions and feature flags;
- resolve support tickets;
- block/unblock users;
- review safety events.

## 4. Core city flow

The city flow is the first release-critical flow.

Required end-to-end chain:

1. Passenger creates order.
2. Backend validates passenger role and payload.
3. Backend calculates recommended price, distance and ETA when coordinates exist.
4. Order becomes active.
5. Only verified, online, available drivers in matching country/city can see or receive it.
6. Driver can accept or counteroffer.
7. Passenger can accept a counteroffer.
8. Backend creates CityTrip.
9. Order status and trip status stay synchronized.
10. Passenger and driver both see current trip.
11. Only assigned driver can update trip status.
12. Passenger can observe status but cannot control it.
13. Completed trip updates history, rating eligibility and finance.

## 5. Core city statuses

Order statuses:

- draft
- active
- accepted
- in_progress
- completed
- cancelled
- expired
- disputed

Trip statuses:

- accepted
- driver_on_way
- driver_arrived
- in_progress
- completed
- cancelled
- disputed

Allowed city trip transitions:

- accepted -> driver_on_way
- accepted -> driver_arrived
- driver_on_way -> driver_arrived
- driver_arrived -> in_progress
- in_progress -> completed
- accepted / driver_on_way / driver_arrived / in_progress -> cancelled

## 6. Driver availability rules

A driver can receive or accept a city order only if all are true:

- user exists;
- user is verified;
- active_role is driver;
- driver is online;
- driver is not blocked;
- driver has no active city trip;
- driver country matches order country;
- driver city matches order city unless explicit cross-city mode is enabled.

## 7. Pricing rules

Every price-related screen must show:

- passenger offered price;
- recommended price;
- currency;
- approximate distance;
- approximate trip time;
- commission policy when relevant.

Intaxi price model:

- passenger may offer own price;
- driver may accept or counteroffer;
- system should warn when price is below reasonable minimum;
- final price is locked when trip is accepted;
- driver cannot demand extra after accepting without creating a support-dispute event.

## 8. Commission and wallet

Initial commission target: low and transparent, configurable per country, with ability to set maximum commission.

Wallet requirements:

- driver balance;
- commission due;
- topup request;
- admin approve/reject topup;
- transaction ledger;
- trip-related commission transaction;
- manual admin adjustment with audit trail.

No balance mutation may happen without a ledger entry.

## 9. Safety requirements

Minimum V2 safety layer:

- driver verification;
- vehicle verification;
- driver card shown to passenger;
- passenger card shown to driver;
- trip sharing link;
- support button on active trip;
- complaint after trip;
- two-way rating;
- block/report user;
- support ticket connected to trip_id;
- admin safety review.

Later safety upgrades:

- pickup PIN;
- trusted contacts;
- suspicious stop detection;
- route deviation detection;
- driver shift time limit;
- women mode.

## 10. Intercity flow

Intercity is separate from city but must use the same principles:

- passenger request;
- driver route;
- price/counteroffer;
- accepted intercity trip;
- chat only after allowed event;
- history;
- support;
- rating.

## 11. Country configuration

No country-specific logic should be scattered across handlers.

Country config must include:

- country code;
- display names;
- currency;
- default tariff per km;
- minimum fare;
- commission policy;
- supported cities/regions;
- map provider preference;
- phone format;
- driver document requirements;
- enabled features.

Initial countries:

- UZ
- TR
- SA
- KZ

## 12. Release quality definition

A feature is done only when it works in:

- database;
- backend service;
- API endpoint;
- Mini App screen;
- Telegram bot flow or notification where needed;
- admin visibility where relevant;
- history/audit;
- error handling;
- tests or smoke-check script.

No UI-only feature is considered complete.
No endpoint-only feature is considered complete.
No bot-only logic is allowed when the same business action exists in Mini App.

## 13. V2 implementation policy

V2 should be built as a clean core, using old files only when they exactly match this specification and do not duplicate business logic.

Hotfix/runtime patch style must be removed from the final architecture.

Acceptable temporary strategy:

- keep current project untouched in main;
- build V2 branch/module cleanly;
- migrate old UI/components only after review;
- replace old flows gradually with V2 services.

## 14. First build target

First implementation target is City MVP V2:

- clean backend domain models;
- city order service;
- driver availability service;
- city trip service;
- pricing service;
- wallet ledger base;
- Telegram notification adapter;
- Mini App API contract;
- smoke test for passenger -> driver -> trip -> completed.
