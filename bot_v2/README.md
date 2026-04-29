# Intaxi Bot V2

Telegram bot V2 is an adapter, not the business core.

## Rules

- Bot must not duplicate pricing, matching, status transition or wallet logic.
- Bot calls Backend V2 API/client.
- Bot sends notifications, deep links and quick actions.
- Mini App remains the full interface for order/trip/admin flows.

## First responsibilities

- Send city order notifications to eligible drivers.
- Provide quick accept / counteroffer / status action buttons.
- Send current trip deep links.
- Provide admin alert buttons that call admin APIs.
