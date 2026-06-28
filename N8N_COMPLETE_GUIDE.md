# 🎯 N8N Instance Setup - Complete Guide

**Ngày tạo**: June 14, 2026  
**Tình trạng**: ✅ 100% Ready to Deploy

---

## TL;DR - Chỉ 5 Phút

```bash
# 1. Start everything
cd backend
docker-compose up -d

# 2. Access N8N → Create account
# http://localhost:5678

# 3. Import workflow
bash ../scripts/import_n8n_workflow.sh

# 4. Setup Telegram
bash ../scripts/setup_telegram.sh

# 5. Test
bash ../scripts/test_n8n_webhook.sh

# Done! ✅
```

---

## 📚 Documentation Map

### 🟢 **START HERE**

- **`N8N_QUICKSTART.md`** - Quick start guide (5 min)

### 🔵 **Detailed Guides**

- **`docs/N8N_HOW_TO_RUN.md`** - Complete "How to run" with all options
- **`docs/N8N_SETUP_GUIDE.md`** - Full setup guide with troubleshooting
- **`docs/N8N_NOTIFICATIONS_STATUS.md`** - Implementation status & checklist

### 🟡 **Setup Scripts**

- **`scripts/setup_n8n.sh`** - Start all Docker services
- **`scripts/import_n8n_workflow.sh`** - Import workflow to N8N
- **`scripts/setup_telegram.sh`** - Interactive Telegram setup
- **`scripts/test_n8n_webhook.sh`** - Test webhook endpoint

### 📋 **Reference**

- **`docs/N8N_ADMIN_NOTIFICATIONS.md`** - Old reference (for history)

---

## 🚀 How to Run N8N Instance

### **Method 1: Automatic Setup** (Recommended - 2 minutes)

```bash
# From project root
bash scripts/setup_n8n.sh

# This automatically:
# ✅ Checks Docker installed
# ✅ Pulls latest images
# ✅ Starts PostgreSQL
# ✅ Starts N8N
# ✅ Starts Backend
# ✅ Shows URLs
```

### **Method 2: Manual Step-by-Step**

#### Step 1: Start Docker Services

```bash
cd backend
docker-compose up -d

# Verify services running
docker-compose ps

# Expected:
# ai_chat_bot_db       | Up 1 minute  | 0.0.0.0:5433->5432/tcp
# ai_chat_bot_n8n      | Up 1 minute  | 0.0.0.0:5678->5678/tcp
# ai_chat_bot_backend  | Up 1 minute  | 0.0.0.0:8001->8000/tcp
```

#### Step 2: Access N8N Dashboard

Open: **http://localhost:5678**

- First time: Create admin account
- Login with credentials

#### Step 3: Import Workflow

**Option A: Automatic (Recommended)**

```bash
bash ../scripts/import_n8n_workflow.sh
```

**Option B: Via UI**

1. Dashboard → Workflows → + New Workflow
2. Click "..." menu → "Import from file"
3. Select: `docs/n8n/restaurant-admin-notifications.workflow.json`
4. Click Import

**Option C: Via JSON**

1. Copy content of: `docs/n8n/restaurant-admin-notifications.workflow.json`
2. Dashboard → "..." → "Import from JSON"
3. Paste content → Click Import

#### Step 4: Configure Telegram

**Automatic (Interactive)**

```bash
bash ../scripts/setup_telegram.sh

# Prompts you through:
# 1. Create bot with @BotFather
# 2. Get TELEGRAM_BOT_TOKEN
# 3. Get TELEGRAM_CHAT_ID
# 4. Auto-updates .env
# 5. Restarts backend
```

**Manual**

```bash
# 1. Chat @BotFather on Telegram
# 2. Get bot token
# 3. Get admin chat ID
# 4. Edit backend/.env:
   TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TELEGRAM_CHAT_ID=-123456789

# 5. Restart backend
cd backend && docker-compose restart backend
```

#### Step 5: Test Webhook

```bash
bash ../scripts/test_n8n_webhook.sh

# Or manually:
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "booking.created",
    "booking": {
      "id": 1,
      "code": "BK001",
      "guest_name": "Test User"
    }
  }'
```

#### Step 6: Test End-to-End

Create test booking in Django Admin:

```
http://localhost:8001/admin
→ Create superuser if needed
→ Create test booking
→ Check Telegram for notification ✅
```

---

## 🔗 System Flow

```
┌────────────────────────────────────────┐
│  Django Backend (localhost:8001)       │
│  ├─ Booking Model                     │
│  ├─ Django Signal post_save           │
│  └─ notify_admin_booking_event()      │
│     └─ HTTP POST to N8N webhook       │
└────────────────────────────────────────┘
                    ↓
        (HTTP POST to localhost:5678)
                    ↓
┌────────────────────────────────────────┐
│  N8N Instance (localhost:5678)         │
│  ├─ Webhook Receiver                  │
│  ├─ Build Message (JavaScript)        │
│  ├─ Validate Secret Header            │
│  └─ Route to Telegram/Facebook        │
└────────────────────────────────────────┘
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
┌──────────────┐            ┌──────────────────┐
│ Telegram API │            │ Facebook API     │
│ (send msg)   │            │ (optional)       │
└──────────────┘            └──────────────────┘
    ↓                               ↓
┌──────────────┐            ┌──────────────────┐
│ Admin        │            │ Admin            │
│ Notification │            │ Notification     │
│ Received ✅   │            │ (if configured)  │
└──────────────┘            └──────────────────┘
```

---

## ⚙️ Configuration Reference

### Environment Variables

```dotenv
# N8N Configuration (backend/.env)
N8N_ADMIN_NOTIFICATIONS_ENABLED=1
N8N_ADMIN_WEBHOOK_URL=http://localhost:5678/webhook/restaurant-admin-notify
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
N8N_ADMIN_WEBHOOK_TIMEOUT_SECONDS=5

# Telegram (REQUIRED for notifications)
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789

# Facebook (OPTIONAL)
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_ADMIN_PSID=
```

### Docker Compose Services

```yaml
# backend/docker-compose.yml
services:
  db:
    image: ankane/pgvector
    ports:
      - 5433:5432

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

  backend:
    depends_on:
      - db
      - n8n
    ports:
      - 8001:8000
```

### Workflow Structure

```
Workflow: Restaurant Admin Notifications

Nodes:
1. Webhook (path: /restaurant-admin-notify)
   └─ Receives POST from backend
   └─ Validates secret header

2. Build Message (JavaScript)
   └─ Formats booking data
   └─ Creates readable message

3. Secret OK? (Conditional)
   └─ Checks X-N8N-Secret header
   └─ Routes to channels if valid

4. Telegram Sender
   └─ Sends to admin group/user
   └─ Uses TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID

5. Facebook Messenger (Optional)
   └─ Sends to Facebook admin
   └─ Uses FACEBOOK_PAGE_ACCESS_TOKEN + FACEBOOK_ADMIN_PSID
```

---

## 📊 Workflow Events Supported

### Booking Events

```
booking.created       → New booking made
booking.pending       → Status changed to pending
booking.confirmed     → Admin confirmed booking
booking.checked_in    → Guest checked in
booking.completed     → Booking completed
booking.cancelled     → Booking cancelled
```

### Payment Events

```
booking_payment.pending   → Payment awaiting
booking_payment.paid      → Payment successful
booking_payment.failed    → Payment failed
booking_payment.cancelled → Payment cancelled
```

---

## 🧪 Testing

### Test 1: Webhook Endpoint

```bash
# Using provided script
bash scripts/test_n8n_webhook.sh

# Manual curl
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -H "Content-Type: application/json" \
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

# Expected response:
# {"ok": true, "text": "[ADMIN] booking.created (created)\n..."}
```

### Test 2: N8N UI

```
1. N8N Dashboard
2. Workflows → Restaurant Admin Notifications
3. Click "Webhook" node
4. Click "Test" to generate sample
5. Should show execution details
```

### Test 3: Real Booking

```
1. Django Admin: http://localhost:8001/admin
2. Create Booking
3. Django signal fires automatically
4. Backend sends HTTP POST to N8N
5. N8N formats and sends to Telegram
6. Admin receives notification ✅
```

---

## 🔍 Monitoring & Debugging

### View N8N Logs

```bash
# Follow logs in real-time
docker-compose logs n8n -f

# Last 50 lines
docker-compose logs n8n | tail -50
```

### View Backend Logs

```bash
# Follow logs
docker-compose logs backend -f

# Check webhook POST logs
docker-compose logs backend | grep -i webhook
```

### Check N8N Executions

```
N8N Dashboard → Executions tab

Shows:
- Execution time
- Status (Success/Failed)
- Execution details for each node
- Error messages if failed
```

### Check Service Status

```bash
docker-compose ps

# Or with more details
docker-compose ps --no-trunc
```

---

## 🐛 Troubleshooting

### Issue: "Cannot reach N8N at http://localhost:5678"

**Solutions:**

```bash
# Check if running
docker-compose ps

# Check logs
docker-compose logs n8n

# Restart
docker-compose restart n8n

# Check port 5678 available
lsof -i :5678
```

### Issue: Webhook returns 401/403

**Cause:** Secret mismatch  
**Solution:**

```bash
# Verify both secrets match exactly
echo "Backend:" $(grep N8N_ADMIN_WEBHOOK_SECRET backend/.env)
echo "Docker:" $(docker-compose exec n8n env | grep N8N_ADMIN_WEBHOOK_SECRET)

# They must be identical
```

### Issue: Telegram message not received

**Solutions:**

```bash
# 1. Verify bot token is valid
curl -s https://api.telegram.org/botTOKEN/getMe | jq .

# 2. Verify chat ID exists
# - For personal: should be positive number
# - For group: should be negative number

# 3. Check if bot is in group/chat
# - Re-add bot if needed

# 4. Check N8N logs
docker-compose logs n8n | grep -i telegram

# 5. Restart backend
docker-compose restart backend
```

### Issue: Workflow not importing

**Solutions:**

```bash
# 1. Check file exists
ls -l docs/n8n/restaurant-admin-notifications.workflow.json

# 2. Check N8N is responding
curl -s http://localhost:5678/api/v1/workflows | jq .

# 3. Try re-import
bash scripts/import_n8n_workflow.sh

# 4. Check N8N logs
docker-compose logs n8n | grep -i import
```

---

## 📈 Performance Notes

- **Webhook Timeout:** 5 seconds (configurable)
- **Message Format:** JSON payload ~1-2 KB
- **Telegram Rate Limit:** 30 messages/second per bot
- **N8N Execution:** Typically <500ms per webhook

---

## 🔐 Security

### Secret Validation

- Backend sends `X-N8N-Secret` header
- N8N validates against `N8N_ADMIN_WEBHOOK_SECRET`
- Must match exactly to process webhook

### HTTPS Setup (For Production)

```
If deploying publicly:
1. Use HTTPS URL in N8N_ADMIN_WEBHOOK_URL
2. Set up SSL certificate
3. N8N webhook can verify HTTPS origin
```

---

## 📋 Setup Checklist

Before going live:

- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL running (port 5433)
- [ ] Backend running (port 8001)
- [ ] N8N running (port 5678)
- [ ] N8N accessible via browser
- [ ] Admin account created in N8N
- [ ] Workflow imported successfully
- [ ] Telegram bot created (@BotFather)
- [ ] TELEGRAM_BOT_TOKEN set in .env
- [ ] TELEGRAM_CHAT_ID set in .env
- [ ] Backend restarted after .env change
- [ ] Webhook test passes (`test_n8n_webhook.sh`)
- [ ] Test booking created
- [ ] Telegram notification received ✅
- [ ] N8N Executions tab shows success

---

## 🚀 Next Steps

### After Setup Complete:

1. **Monitor Production**
   - Watch N8N Executions dashboard
   - Monitor webhook delivery
   - Check for failures

2. **Optimize**
   - Adjust timeout if needed
   - Customize message format
   - Add more channels (Discord, Slack)

3. **Scale**
   - Setup N8N clustering
   - Use managed N8N service
   - Add redundancy

4. **Integrate**
   - Add more workflow triggers
   - Implement advanced routing
   - Connect to other services

---

## 📞 Support & Resources

- **N8N Docs**: https://docs.n8n.io/
- **N8N Community**: https://community.n8n.io/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Docker Docs**: https://docs.docker.com/

---

## ✅ Summary

**What's Setup:**

- ✅ Docker Compose with N8N, Backend, PostgreSQL
- ✅ N8N workflow JSON (imported via script)
- ✅ Webhook endpoint secured with secret
- ✅ Django signals integrated
- ✅ Telegram bot support
- ✅ Comprehensive setup scripts
- ✅ Full documentation

**What's Ready:**

- ✅ Production-ready code
- ✅ Automated setup scripts
- ✅ Complete documentation
- ✅ Test utilities
- ✅ Troubleshooting guides

**What You Need to Do:**

1. Run: `bash scripts/setup_n8n.sh`
2. Run: `bash scripts/setup_telegram.sh`
3. Run: `bash scripts/test_n8n_webhook.sh`
4. Create test booking
5. Verify Telegram notification ✅

**Time to Completion:** 5-10 minutes

---

## 🎉 Ready to Deploy?

```bash
cd /home/levansy/DATN/demo-chat-bot
bash scripts/setup_n8n.sh
```

**That's it!** You're now ready to receive admin notifications on Telegram. 🎊
