# Intaxi V2 State Machine

## 1. Core rule

Status transitions are owned by backend services only.

Mini App, bot and admin interfaces may request a transition, but they must not directly mutate status fields or implement separate transition logic.

## 2. City order statuses

```text
draft
active
accepted
in_progress
completed
cancelled
expired
disputed
```

### City order transition table

```text
draft      -> active, cancelled
active     -> accepted, cancelled, expired, disputed
accepted   -> in_progress, cancelled, disputed
in_progress -> completed, cancelled, disputed
completed  -> disputed
cancelled  -> disputed
expired    -> active, disputed
disputed   -> completed, cancelled
```

## 3. City trip statuses

```text
accepted
driver_on_way
driver_arrived
in_progress
completed
cancelled
disputed
```

### City trip transition table

```text
accepted        -> driver_on_way, driver_arrived, cancelled, disputed
driver_on_way   -> driver_arrived, cancelled, disputed
driver_arrived  -> in_progress, cancelled, disputed
in_progress     -> completed, cancelled, disputed
completed       -> disputed
cancelled       -> disputed
disputed        -> completed, cancelled
```

## 4. Intercity statuses

Intercity uses the same general lifecycle but can skip city-specific arrival steps depending on product mode.

```text
active
accepted
driver_on_way
in_progress
completed
cancelled
expired
disputed
```

Allowed intercity transitions:

```text
active        -> accepted, cancelled, expired, disputed
accepted      -> driver_on_way, in_progress, cancelled, disputed
driver_on_way -> in_progress, cancelled, disputed
in_progress   -> completed, cancelled, disputed
completed     -> disputed
cancelled     -> disputed
expired       -> active, disputed
disputed      -> completed, cancelled
```

## 5. Driver verification statuses

```text
not_started
pending
approved
rejected
suspended
```

Rules:

- only approved drivers can go online;
- suspended drivers are treated as unavailable;
- rejected drivers can resubmit only through explicit resubmission flow.

## 6. Driver online statuses

Driver online state is not only `is_online`.

Effective availability is computed as:

```text
is_verified == true
and is_blocked == false
and is_online == true
and is_busy == false
and no active trip exists
and country/city matches
and mode eligibility matches
```

A driver may be online but not available if busy.

## 7. Women mode eligibility

Women mode city order creation requires:

```text
user.gender == female
user.is_adult_confirmed == true
mode == women
```

Women mode driver matching requires:

```text
driver.gender == female
driver.is_adult_confirmed == true
driver_profile.status == approved
driver_profile.is_woman_driver_verified == true
driver_profile.woman_driver_status == approved
driver is online and available
```

## 8. Payment topup statuses

```text
pending
approved
rejected
cancelled
```

Allowed transitions:

```text
pending -> approved, rejected, cancelled
approved -> no transition
rejected -> no transition
cancelled -> no transition
```

Approving a topup must create wallet ledger credit entry.

## 9. Commission rule status

Commission rules are controlled by `is_active`, `starts_at`, `ends_at` and scope.

Resolution order:

```text
driver override
city rule
country rule
global rule
fallback 0%
```

## 10. Support ticket statuses

```text
open
in_review
waiting_user
resolved
rejected
closed
```

Allowed transitions:

```text
open -> in_review, waiting_user, resolved, rejected, closed
in_review -> waiting_user, resolved, rejected, closed
waiting_user -> in_review, resolved, rejected, closed
resolved -> closed, in_review
rejected -> closed, in_review
closed -> no transition
```

## 11. Status synchronization rules

City trip status changes must update related city order:

```text
trip.accepted        -> order.accepted
trip.driver_on_way   -> order.accepted
trip.driver_arrived  -> order.accepted
trip.in_progress     -> order.in_progress
trip.completed       -> order.completed
trip.cancelled       -> order.cancelled
trip.disputed        -> order.disputed
```

The reverse must not happen blindly. Order changes should call service methods that know whether a trip exists.

## 12. Invalid transition behavior

Invalid transitions must return a structured error:

```json
{
  "error": {
    "code": "invalid_status_transition",
    "message": "Invalid status transition",
    "details": {
      "from": "accepted",
      "to": "completed"
    }
  }
}
```
