# n8n admin notifications

Backend now sends admin notification events to n8n when:

- a booking is created or updated
- a booking payment is created or updated
- SePay IPN marks a payment paid, void, or updates payment metadata

## Run n8n with the project

From the backend folder:

```bash
cd demo-chat-bot/backend
docker compose up -d db n8n backend
```

Open n8n:

```text
http://localhost:5678
```

The backend container calls n8n at:

```text
http://n8n:5678/webhook/restaurant-admin-notify
```

If you run Django directly on your host instead of Docker, keep this value in `backend/.env`:

```text
N8N_ADMIN_WEBHOOK_URL=http://localhost:5678/webhook/restaurant-admin-notify
```

## Import workflow

1. Open n8n at `http://localhost:5678`.
2. Create your owner account if n8n asks.
3. Go to `Workflows` -> `Import from File`.
4. Import `docs/n8n/restaurant-admin-notifications.workflow.json`.
5. Fill environment variables in `backend/.env`:

```text
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_ADMIN_PSID=
```

6. Restart n8n after changing env values:

```bash
cd demo-chat-bot/backend
docker compose up -d n8n
```

7. In n8n, open the workflow and click `Active`.

If you only want Telegram, disable the `Send Facebook Messenger` node. If you only want Facebook, disable the `Send Telegram` node.

## Test webhook

With the workflow active:

```bash
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H 'Content-Type: application/json' \
  -H 'X-N8N-Secret: change-this-n8n-secret' \
  -d '{
    "event": "booking.changed",
    "action": "created",
    "restaurant": {"name": "PSCD Japanese Dining"},
    "booking": {
      "code": "TEST1234",
      "guest_name": "Nguyen Van A",
      "guest_phone": "0900000000",
      "booking_date": "2026-04-28",
      "booking_time": "19:00",
      "party_size": 4,
      "status_label": "Cho thanh toan",
      "table": {"id": 1, "floor": 1, "table_type_label": "Standard"}
    },
    "payment": {"status_label": "Cho thanh toan", "amount": 100000, "currency": "VND"}
  }'
```

## Telegram setup

1. Create a bot with `@BotFather`.
2. Put the bot token into `TELEGRAM_BOT_TOKEN`.
3. Send a message to the bot from the target admin account/group.
4. Get `TELEGRAM_CHAT_ID` from:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

## Facebook setup

The sample workflow uses Messenger Send API through an HTTP Request node. You need:

- `FACEBOOK_PAGE_ACCESS_TOKEN`
- `FACEBOOK_ADMIN_PSID`, the Page-scoped ID of the admin/user who should receive the message

Meta requires the recipient to have previously interacted with the Page, and app permissions may be required before production use.
