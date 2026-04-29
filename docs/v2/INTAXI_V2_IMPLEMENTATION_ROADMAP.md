# Intaxi V2 Implementation Roadmap

## Phase 0. Freeze legacy hotfix growth

- Do not add new runtime monkey patches.
- Do not add duplicated business logic to bot handlers.
- Keep current main stable until V2 is ready.

## Phase 1. V2 foundation

Deliverables:

- master specification;
- product decisions;
- architecture plan;
- data model;
- API contract;
- state machine;
- implementation roadmap;
- backend skeleton.

Exit criteria:

- all core statuses centralized;
- all core errors centralized;
- all business services have stub interfaces;
- tests folder exists with city flow smoke-test skeleton.

## Phase 2. Backend core

Build:

- FastAPI app shell;
- settings/config;
- async SQLAlchemy database setup;
- Alembic skeleton;
- domain statuses;
- domain exceptions;
- country config service;
- commission service;
- pricing service;
- driver availability service;
- city order service;
- city trip service;
- wallet ledger service.

Exit criteria:

- backend imports without side effects;
- no bot import required for backend startup;
- service methods are testable without Telegram;
- city order/trip core can run in unit tests.

## Phase 3. City MVP V2

Build complete city flow:

1. passenger creates city order;
2. matching drivers are computed;
3. driver sees available order;
4. driver accepts or counteroffers;
5. passenger accepts counteroffer;
6. city trip is created;
7. current trip endpoint works for both sides;
8. driver status transitions work;
9. passenger cannot update status;
10. order/trip statuses stay synchronized;
11. completed trip writes history and optional commission ledger.

Exit criteria:

- smoke test passes;
- API responses match contract;
- no direct DB status mutation outside service layer.

## Phase 4. Women mode V2

Build:

- gender/adult confirmation profile fields;
- women mode order creation;
- women mode driver verification;
- women mode matching filter;
- women mode UI theme flag;
- admin approve woman driver action.

Exit criteria:

- non-eligible passenger cannot create women mode order;
- non-approved woman driver cannot see women mode orders;
- regular mode is unaffected.

## Phase 5. Mini App V2 connection

Build/replace screens:

- profile;
- driver registration;
- driver online/offline;
- city create;
- city available orders;
- counteroffers;
- current trip;
- driver payment details button;
- support button;
- rating after trip;
- women mode toggle/design.

Exit criteria:

- no page owns business status rules;
- UI calls V2 API only;
- all role/mode checks are backend-enforced.

## Phase 6. Bot V2 connection

Build bot as API client:

- auth/session binding;
- deep links to Mini App;
- city order notifications;
- driver accept quick action;
- counteroffer quick action;
- trip status quick action;
- current trip link;
- admin urgent actions.

Exit criteria:

- bot does not duplicate matching/pricing/status logic;
- bot only calls API/client layer;
- Telegram messages and Mini App show same state.

## Phase 7. Admin V2

Build synchronized admin surfaces:

Mini App admin:

- dashboard;
- driver verification;
- woman driver verification;
- vehicles;
- orders/trips;
- commission settings;
- wallet/topups;
- support tickets;
- audit log.

Bot admin:

- urgent approvals;
- payment alerts;
- support alerts;
- driver verification quick approve/reject;
- links into Mini App admin.

Exit criteria:

- admin changes go through API;
- admin actions are audit logged;
- commission changes are traceable.

## Phase 8. Intercity V2

Build:

- passenger intercity request;
- driver intercity route;
- matching;
- accept/counteroffer;
- intercity trip;
- chat/support/rating/history;
- women mode for intercity.

Exit criteria:

- intercity uses shared user/driver/wallet/support primitives;
- city flow remains stable.

## Phase 9. Production hardening

Build:

- Docker production layout;
- env validation;
- Alembic migrations;
- logs;
- healthchecks;
- backup script;
- rollback plan;
- CI checks;
- smoke tests;
- release checklist.

Exit criteria:

- deploy can be repeated;
- rollback is documented;
- no secrets in repo;
- healthcheck confirms API/DB.

## Phase 10. Legacy cleanup

Remove or archive:

- runtime patches;
- hotfix files;
- duplicate bot DB business logic;
- old endpoints replaced by V2;
- unused components.

Exit criteria:

- V2 is the only active business flow;
- old code cannot accidentally handle production orders.
