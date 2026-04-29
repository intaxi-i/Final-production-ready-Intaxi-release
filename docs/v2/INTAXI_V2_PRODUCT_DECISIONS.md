# Intaxi V2 Product Decisions

This document fixes the product and technical decisions confirmed for the clean V2 rebuild.

## 1. Technology stack

Backend:

- FastAPI
- PostgreSQL
- SQLAlchemy async
- Alembic migrations

Bot:

- aiogram

Mini App:

- Next.js / React

Admin:

- synchronized admin panel in Mini App;
- admin bot controls for urgent actions and notifications;
- both admin surfaces must use the same backend/admin APIs.

## 2. Interface strategy

Chosen strategy: Mini App is the full product interface. Bot is notification, quick action and fallback layer.

Meaning:

- city/intercity orders and trips work fully in Mini App;
- bot sends notifications, deep links and fast actions;
- bot must not own separate business logic;
- if bot offers an action, it must call the same backend/service rules as Mini App.

## 3. Commission strategy

Initial commission is 0%.

Commission must be configurable from admin panel.

Commission settings must support:

- global default commission;
- country-level commission;
- city-level commission;
- driver-level override;
- first N rides without commission;
- start/end date for promo commission;
- active/inactive toggle;
- full audit log of who changed commission and when.

Commission must not be hardcoded.

When commission becomes non-zero, it should be calculated after trip completion and recorded through wallet ledger.

No balance mutation is allowed without ledger entry.

## 4. First payment model

MVP payment model:

- passenger pays driver directly by cash or manual transfer;
- passenger decides payment method;
- driver may add card number/payment details;
- during trip or at completion passenger can tap a button to view driver card/payment details;
- Intaxi only tracks trip price, final agreed price, commission rules and driver balance/ledger.

Online acquiring/card processing is not part of first release.

## 5. Driver card/payment details

Driver may specify payment details such as card number.

Rules:

- payment details are visible to passenger only for assigned active trip or just-completed trip;
- driver payment details must not be shown in public order lists;
- access must be checked by trip participant relationship;
- admin can view/edit/disable driver payment details if needed.

## 6. Women mode

Women mode is included from V2, not postponed.

Goal:

- same flow as regular city/intercity mode;
- only women passengers and women drivers participate;
- separate visual mode in Mini App with more feminine design;
- separate filters and matching rules;
- admin verification is required for women drivers;
- women passengers can enter women mode without driver-style verification, but must confirm eligibility.

Required profile fields:

- gender: female / male / unspecified;
- adult confirmation: yes/no;
- no exact birth date is required for MVP;
- women driver verification status;
- admin review fields for women driver approval.

Women mode matching rules:

- passenger must choose women mode;
- passenger profile must be eligible for women mode;
- driver must be verified as woman driver;
- only women drivers can see women-mode orders;
- only women passengers can create women-mode orders.

## 7. City and intercity priority

City flow must be built perfectly first because it is the core flow.

Intercity must also be part of V2 and should be designed immediately, but implementation can be sequenced after the city core if needed.

The architecture must support both from the beginning:

- shared users;
- shared driver availability;
- shared pricing rules where possible;
- shared wallet/commission;
- shared support/rating;
- separate city/intercity order and trip logic.

## 8. Rewrite policy

Default approach: clean rebuild.

Old files/components can be reused only after strict review and only if they fully match V2 architecture.

Allowed reuse:

- UI components that are clean and generic;
- location/country data if verified;
- map picker if it fits V2 contract;
- useful schemas only after normalization.

Not allowed:

- runtime monkey patches;
- hotfix business logic;
- duplicated bot/Mini App flows;
- direct DB business actions from bot handlers;
- hardcoded commission;
- hardcoded country-specific business rules scattered across files.

## 9. Build principle

Build as one system:

DB -> Backend services -> API -> Mini App -> Bot notifications/actions -> Admin -> History -> Support -> Logs.

A feature is not complete until it works across the whole relevant chain.
