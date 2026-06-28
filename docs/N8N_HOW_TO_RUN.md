# 🎯 N8N Notifications - How to Run

## ⚡ Cách Chạy N8N Instance & Import Workflow

### **Option 1: Full Automatic Setup** (Khuyên dùng - 2 phút)

```bash
# 1. Navigate to project
cd /home/levansy/DATN/demo-chat-bot

# 2. Run full setup script
bash scripts/setup_n8n.sh

# This automatically:
# ✅ Checks Docker/Docker Compose installed
# ✅ Stops old containers
# ✅ Starts PostgreSQL, Backend, N8N
# ✅ Waits for services ready
# ✅ Shows next steps
```

**Sau khi script chạy xong:**

```
Dashboard: http://localhost:5678
Backend: http://localhost:8001
Database: localhost:5433
```

---

### **Option 2: Manual Step-by-Step**

#### Step 1: Start Services

```bash
cd backend
docker-compose up -d

# Verify
docker-compose ps
```

#### Step 2: Access N8N

- Open: http://localhost:5678
- Create admin account (first time)
- Login to dashboard

#### Step 3: Import Workflow

**Method A: Automatic Script** (recommended)

```bash
bash ../scripts/import_n8n_workflow.sh
```

**Method B: Manual via UI**

1. N8N Dashboard → "Workflows" → "+ New Workflow"
2. Click "..." menu → "Import from file"
3. Select: `docs/n8n/restaurant-admin-notifications.workflow.json`
4. Click "Import"

**Method C: Copy-Paste JSON**

1. N8N Dashboard → "..." menu → "Import from JSON"
2. Open file: `docs/n8n/restaurant-admin-notifications.workflow.json`
3. Copy entire content and paste into N8N
4. Click "Import"

#### Step 4: Setup Telegram

```bash
bash scripts/setup_telegram.sh

# Interactive guide will:
# 1. Tell you to chat @BotFather on Telegram
# 2. Walk through creating bot
# 3. Ask for TELEGRAM_BOT_TOKEN
# 4. Ask for TELEGRAM_CHAT_ID
# 5. Auto-update backend/.env
# 6. Restart backend
```

Or **manual setup:**

```bash
# Edit backend/.env
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789

# Restart backend
cd backend && docker-compose restart backend
```

#### Step 5: Test Webhook

```bash
bash scripts/test_n8n_webhook.sh

# Expected output:
# ✅ Webhook test successful!
# Next steps:
# 1. Check N8N Dashboard → Executions
# 2. Should see execution entry for this webhook
```

Or **curl test:**

```bash
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "booking.created",
    "booking": {
      "id": 1,
      "code": "BK001",
      "guest_name": "Test"
    }
  }'

# Should return: {"ok": true, "text": "..."}
```

#### Step 6: Test End-to-End

```bash
# Option A: Via Django Admin
http://localhost:8001/admin
→ Create superuser (if needed)
→ Create test booking
→ Check Telegram for notification

# Option B: Via API
curl -X POST http://localhost:8001/api/restaurant/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "guest_name": "Test User",
    "guest_phone": "0901234567",
    "booking_date": "2026-06-15",
    "booking_time": "19:00",
    "party_size": 2,
    "source": "web"
  }'
```

---

## 🔗 Architecture Flow

```
Django Backend (localhost:8001)
  ↓
  Create/Update Booking
  ↓
  Django Signal → post_save
  ↓
  notify_admin_booking_event()
  ↓
  HTTP POST to N8N Webhook
  ↓
N8N Instance (localhost:5678)
  ↓
  Webhook Receiver
  ↓
  Build Message (JavaScript)
  ↓
  Check Secret Header
  ↓
  Send to Telegram/Facebook
  ↓
Admin receives notification ✅
```

---

## 📦 What Gets Deployed

### In Docker:

- **N8N** (image: n8nio/n8n:latest)
  - Port: 5678
  - Mounts: N8N workflows, credentials
- **Backend** (Django + Gunicorn)
  - Port: 8001
  - Depends on: N8N, PostgreSQL
- **PostgreSQL** (image: ankane/pgvector)
  - Port: 5433
  - Volumes: Database data

### Configuration:

- Environment variables from `backend/.env`
- N8N secret validation
- Telegram bot credentials
- Webhook timeout: 5 seconds

---

## ⚙️ Configuration Reference

### `.env` Variables Needed

```dotenv
# N8N (already set, don't change)
N8N_ADMIN_NOTIFICATIONS_ENABLED=1
N8N_ADMIN_WEBHOOK_URL=http://localhost:5678/webhook/restaurant-admin-notify
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
N8N_ADMIN_WEBHOOK_TIMEOUT_SECONDS=5

# Telegram (need to fill these)
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789

# Optional (Facebook)
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_ADMIN_PSID=
```

### Workflow Nodes

1. **Webhook Node**
   - Path: `/restaurant-admin-notify`
   - Method: POST
   - Response: JSON with processed message

2. **Build Message Node**
   - JavaScript code
   - Formats booking data for display
   - Validates secret header

3. **Secret Check Node**
   - Validates `X-N8N-Secret` header
   - Compares with `N8N_ADMIN_WEBHOOK_SECRET`

4. **Telegram Node** (or Facebook)
   - Sends formatted message
   - Uses `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`
   - Or Facebook credentials

---

## 🐛 Common Issues & Fixes

### N8N not starting?

```bash
# Check port 5678 is free
lsof -i :5678

# Kill if needed
kill -9 <PID>

# Restart
docker-compose restart n8n
```

### Workflow import fails?

```bash
# Check N8N logs
docker-compose logs n8n | tail -50

# Try re-import
bash scripts/import_n8n_workflow.sh

# Or import via UI manually
```

### Telegram not working?

```bash
# Verify token
curl -s https://api.telegram.org/botTOKEN/getMe | jq .

# Check chat ID exists
# Send test message to group

# Restart backend with new credentials
docker-compose restart backend
```

### Webhook returns 401?

```bash
# Secret mismatch - check both:
echo "Backend .env:" $(grep N8N_ADMIN_WEBHOOK_SECRET backend/.env)
echo "Docker env:" $(docker-compose exec n8n env | grep N8N_ADMIN_WEBHOOK_SECRET)

# They must match exactly
```

---

## 📊 Verification Checklist

- [ ] N8N Dashboard accessible: http://localhost:5678
- [ ] Admin account created in N8N
- [ ] Workflow imported: "Restaurant Admin Notifications"
- [ ] Workflow shows 5 nodes connected properly
- [ ] Telegram bot token set in `backend/.env`
- [ ] Telegram chat ID set in `backend/.env`
- [ ] Backend restarted after `.env` change
- [ ] Webhook test succeeds: `test_n8n_webhook.sh`
- [ ] Test booking created
- [ ] Telegram notification received ✅

---

## 📚 Useful Commands

```bash
# View all running containers
docker-compose ps

# View N8N logs
docker-compose logs n8n -f

# View backend logs
docker-compose logs backend -f

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart n8n

# Stop everything
docker-compose down

# See N8N executions
# → N8N Dashboard → Executions tab

# Test webhook
bash scripts/test_n8n_webhook.sh

# Re-import workflow
bash scripts/import_n8n_workflow.sh

# Setup Telegram
bash scripts/setup_telegram.sh
```

---

## 🎯 Next Steps After Setup

1. **Telegram notifications working?**
   - ✅ Yes → Move to production deployment
   - ❌ No → Run `test_n8n_webhook.sh` and check logs

2. **Ready for more features?**
   - Add Facebook Messenger notifications
   - Add Slack/Discord notifications
   - Setup webhook filtering
   - Add custom message templates

3. **Production deployment:**
   - Use persistent N8N database
   - Setup SSL/TLS for webhooks
   - Configure backup strategy
   - Monitor webhook delivery

---

## 📞 Support

- **N8N Docs**: https://docs.n8n.io/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Docker Docs**: https://docs.docker.com/
