# 🚀 N8N Admin Notifications - Quick Start

Hướng dẫn nhanh để setup N8N instance và import workflow for admin notifications.

---

## ⚡ Quick Setup (5 phút)

### 1️⃣ Start All Services

```bash
cd backend
docker-compose up -d

# Verify services running
docker-compose ps
# Should show: n8n (port 5678), backend (port 8001), db (port 5433)
```

### 2️⃣ Access N8N Dashboard

Open: **http://localhost:5678**

- Create admin account (first time only)
- Login

### 3️⃣ Import Workflow

```bash
# Option A: Automatic import
bash ../scripts/import_n8n_workflow.sh

# Option B: Manual via UI
# N8N Dashboard → Workflows → "..." → "Import from file"
# Select: docs/n8n/restaurant-admin-notifications.workflow.json
```

### 4️⃣ Setup Telegram Bot

```bash
bash ../scripts/setup_telegram.sh
```

This script will:

- Guide you to create a Telegram bot via @BotFather
- Help get TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
- Auto-update `backend/.env`
- Restart backend

### 5️⃣ Test Webhook

```bash
bash ../scripts/test_n8n_webhook.sh

# Or curl manually
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "booking.created",
    "booking": {
      "id": 1,
      "code": "BK001",
      "guest_name": "Test User",
      "status": "pending"
    }
  }'
```

### 6️⃣ Test with Real Booking

1. Go to Django Admin: http://localhost:8001/admin
2. Create superuser (if needed):
   ```bash
   python manage.py createsuperuser
   ```
3. Create a test booking
4. Check Telegram for notification ✅

---

## 📚 Detailed Guides

- **Full Setup Guide**: [N8N_SETUP_GUIDE.md](../docs/N8N_SETUP_GUIDE.md)
- **Notification Status**: [N8N_NOTIFICATIONS_STATUS.md](../docs/N8N_NOTIFICATIONS_STATUS.md)

---

## 📁 Available Scripts

### Setup Scripts

#### 1. `setup_n8n.sh` - Complete Docker Setup

```bash
bash scripts/setup_n8n.sh

# Automatically:
# ✅ Checks Docker/Docker Compose
# ✅ Starts all services (PostgreSQL, Backend, N8N)
# ✅ Displays next steps
```

#### 2. `import_n8n_workflow.sh` - Import Workflow

```bash
bash scripts/import_n8n_workflow.sh [N8N_URL]

# Default: http://localhost:5678
# Example with custom URL:
bash scripts/import_n8n_workflow.sh http://n8n-prod.example.com
```

#### 3. `setup_telegram.sh` - Telegram Bot Configuration

```bash
bash scripts/setup_telegram.sh

# Guides through:
# 1. Creating bot with @BotFather
# 2. Getting TELEGRAM_BOT_TOKEN
# 3. Getting TELEGRAM_CHAT_ID
# 4. Auto-updates backend/.env
# 5. Restarts backend
```

### Test Scripts

#### 4. `test_n8n_webhook.sh` - Test Webhook

```bash
bash scripts/test_n8n_webhook.sh [WEBHOOK_URL] [SECRET]

# Default usage:
bash scripts/test_n8n_webhook.sh

# Custom webhook URL:
bash scripts/test_n8n_webhook.sh http://localhost:5678/webhook/restaurant-admin-notify

# Custom webhook URL + secret:
bash scripts/test_n8n_webhook.sh http://localhost:5678/webhook/restaurant-admin-notify my-secret
```

---

## 🔍 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Django                           │
│                                                             │
│  Booking Model → Signal Post_Save                          │
│                 └─> notify_admin_booking_event()           │
│                     (sends HTTP POST to N8N webhook)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    (HTTP POST webhook)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    N8N Workflow                             │
│                                                             │
│  Webhook Receiver                                           │
│     ↓                                                       │
│  Build Message (JavaScript formatting)                    │
│     ↓                                                       │
│  Check Secret (X-N8N-Secret header validation)            │
│     ↓                                                       │
│  ┌─────────────────────────────────────────┐              │
│  │  ├─ Telegram Sender                     │              │
│  │  └─ Facebook Messenger Sender (optional)│              │
│  └─────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
       ↓ (Telegram API)           ↓ (Facebook API)
   ┌────────────────┐         ┌──────────────────┐
   │  Telegram Bot  │         │  Facebook Bot    │
   │  (Admin Group) │         │  (Optional)      │
   └────────────────┘         └──────────────────┘
```

---

## ⚙️ Configuration Files

### `.env` Variables

```dotenv
# N8N Configuration
N8N_ADMIN_NOTIFICATIONS_ENABLED=1
N8N_ADMIN_WEBHOOK_URL=http://localhost:5678/webhook/restaurant-admin-notify
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
N8N_ADMIN_WEBHOOK_TIMEOUT_SECONDS=5

# Telegram Credentials (required to receive notifications)
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789

# Facebook (optional)
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_ADMIN_PSID=
```

### Docker Compose

```yaml
n8n:
  image: n8nio/n8n:latest
  ports:
    - 5678:5678
  environment:
    - N8N_HOST=localhost
    - N8N_ADMIN_WEBHOOK_SECRET=${N8N_ADMIN_WEBHOOK_SECRET}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
  depends_on:
    - db
```

---

## 🧪 Manual Testing

### Test 1: Webhook Direct Call

```bash
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "Content-Type: application/json" \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -d '{
    "event": "booking.created",
    "action": "created",
    "restaurant": {
      "name": "PSCD Japanese Dining",
      "website_url": "http://localhost:5173"
    },
    "booking": {
      "id": 1,
      "code": "BK001",
      "status": "pending",
      "guest_name": "Nguyễn Văn A",
      "guest_phone": "0901234567",
      "booking_date": "2026-06-15",
      "booking_time": "19:00",
      "party_size": 4
    }
  }'
```

Expected response:

```json
{
  "ok": true,
  "text": "[ADMIN] booking.created (created)\nMã booking: BK001\n..."
}
```

### Test 2: Via Django Admin

```bash
# Open Django admin
http://localhost:8001/admin

# Create superuser
python manage.py createsuperuser

# Create test booking
# → Should automatically trigger webhook
# → Should receive Telegram message
```

### Test 3: Via N8N UI

```
N8N Dashboard
  → Workflows
  → Restaurant Admin Notifications
  → Click "Webhook" node
  → Click "Test"
  → Should show sample execution
```

---

## 🐛 Troubleshooting

### Issue: Cannot reach N8N (http://localhost:5678)

```bash
# Check if container is running
docker-compose ps n8n

# Check N8N logs
docker-compose logs n8n -f

# Restart N8N
docker-compose restart n8n
```

### Issue: Webhook returns error 401/403

```bash
# Check secret matches
echo "Backend secret:" $N8N_ADMIN_WEBHOOK_SECRET
echo "N8N secret:" $N8N_ADMIN_WEBHOOK_SECRET

# They must match exactly
```

### Issue: Telegram message not received

```bash
# Verify credentials
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# Test bot directly
curl -X GET https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe

# Check if bot is in group/chat
# Re-add bot to group if needed
```

### Issue: Workflow not found after import

```bash
# Refresh N8N page
# Or re-import workflow
bash scripts/import_n8n_workflow.sh

# Check N8N logs for import errors
docker-compose logs n8n | grep -i import
```

---

## 📊 Event Types

### Booking Events

- `booking.created` - New booking made
- `booking.confirmed` - Booking confirmed by admin
- `booking.checked_in` - Guest checked in
- `booking.completed` - Booking completed
- `booking.cancelled` - Booking cancelled

### Payment Events

- `booking_payment.pending` - Payment awaiting
- `booking_payment.paid` - Payment successful
- `booking_payment.failed` - Payment failed
- `booking_payment.cancelled` - Payment cancelled

---

## 🎯 Next Steps

1. ✅ Run `setup_n8n.sh` to start services
2. ✅ Run `setup_telegram.sh` to configure Telegram
3. ✅ Run `test_n8n_webhook.sh` to verify setup
4. ✅ Create test booking to verify end-to-end

Once verified, N8N will automatically:

- Receive webhook from backend
- Validate security headers
- Format message
- Send to Telegram/Facebook

---

## 📚 Documentation

- [Full Setup Guide](../docs/N8N_SETUP_GUIDE.md)
- [Notifications Status](../docs/N8N_NOTIFICATIONS_STATUS.md)
- [N8N Official Docs](https://docs.n8n.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 🆘 Need Help?

1. Check logs: `docker-compose logs -f`
2. Read detailed guides in `docs/`
3. Test webhook: `bash scripts/test_n8n_webhook.sh`
4. Review N8N UI → Executions tab
