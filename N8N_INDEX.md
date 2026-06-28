# 📚 N8N Admin Notifications - Complete Documentation Index

**Last Updated**: June 14, 2026  
**Status**: ✅ Production Ready

---

## 🎯 Quick Navigation

### 🟢 **START HERE** (Choose Based on Your Need)

| If You Want To...               | Read This                                                              | Time   |
| ------------------------------- | ---------------------------------------------------------------------- | ------ |
| **Just get it running ASAP**    | [`N8N_QUICKSTART.md`](N8N_QUICKSTART.md)                               | 5 min  |
| **Understand how to run it**    | [`N8N_COMPLETE_GUIDE.md`](N8N_COMPLETE_GUIDE.md)                       | 15 min |
| **Get detailed step-by-step**   | [`docs/N8N_HOW_TO_RUN.md`](docs/N8N_HOW_TO_RUN.md)                     | 20 min |
| **Full setup with all options** | [`docs/N8N_SETUP_GUIDE.md`](docs/N8N_SETUP_GUIDE.md)                   | 30 min |
| **Check implementation status** | [`docs/N8N_NOTIFICATIONS_STATUS.md`](docs/N8N_NOTIFICATIONS_STATUS.md) | 10 min |
| **See quick reference**         | Run `bash scripts/show_n8n_summary.sh`                                 | 2 min  |

---

## 📁 File Structure

### 📄 Documentation Files (Root)

```
/home/levansy/DATN/demo-chat-bot/
├── N8N_QUICKSTART.md           ← Quick start guide
├── N8N_COMPLETE_GUIDE.md       ← Complete how-to run guide
├── N8N_INDEX.md                ← This file
```

### 📄 Documentation Files (docs/)

```
/docs/
├── N8N_HOW_TO_RUN.md           ← Detailed how to run
├── N8N_SETUP_GUIDE.md          ← Full setup guide with options
├── N8N_NOTIFICATIONS_STATUS.md ← Implementation status & checklist
├── N8N_ADMIN_NOTIFICATIONS.md  ← Old reference (for history)
└── n8n/
    └── restaurant-admin-notifications.workflow.json ← N8N Workflow
```

### 🔧 Setup Scripts (scripts/)

```
/scripts/
├── setup_n8n.sh                ← Start Docker services (Main setup)
├── import_n8n_workflow.sh      ← Import workflow to N8N instance
├── setup_telegram.sh           ← Interactive Telegram bot setup
├── test_n8n_webhook.sh         ← Test webhook endpoint
└── show_n8n_summary.sh         ← Display quick reference
```

### 💻 Implementation Files (backend/)

```
/backend/
├── .env                        ← Configuration (add TELEGRAM_BOT_TOKEN here)
├── docker-compose.yml          ← Docker services (includes N8N)
└── restaurant_booking/
    └── services/
        └── n8n_notifications.py ← Webhook sender service
```

---

## 🚀 Getting Started Flow

```
START
  ↓
1. Choose your path:
   - Quick? → N8N_QUICKSTART.md
   - Detailed? → N8N_COMPLETE_GUIDE.md
   - Full? → docs/N8N_SETUP_GUIDE.md
  ↓
2. Run: bash scripts/setup_n8n.sh
   (Starts Docker services)
  ↓
3. Open: http://localhost:5678
   (Access N8N Dashboard)
  ↓
4. Run: bash scripts/import_n8n_workflow.sh
   (Import workflow)
  ↓
5. Run: bash scripts/setup_telegram.sh
   (Setup Telegram bot)
  ↓
6. Run: bash scripts/test_n8n_webhook.sh
   (Test webhook)
  ↓
7. Create test booking
   (Verify Telegram notification)
  ↓
✅ DONE!
```

---

## 📖 Documentation Details

### `N8N_QUICKSTART.md` (5 minutes)

- Overview of all scripts
- Quick setup (5 min)
- Basic testing

**Best for:** Getting running ASAP

### `N8N_COMPLETE_GUIDE.md` (15 minutes)

- TL;DR quick setup
- Automatic method (recommended)
- Manual step-by-step
- Configuration reference
- Testing procedures
- Troubleshooting
- Monitoring

**Best for:** Understanding how everything works

### `docs/N8N_HOW_TO_RUN.md` (20 minutes)

- Multiple setup options (automatic/manual)
- Detailed architecture diagrams
- Configuration guide
- Testing with curl examples
- Troubleshooting common issues
- Useful Docker commands

**Best for:** Detailed how-to reference

### `docs/N8N_SETUP_GUIDE.md` (30 minutes)

- Complete installation guide
- 6-step process with full details
- System architecture explained
- Event types documentation
- Debug commands
- End-to-end testing
- Telegram bot setup
- Troubleshooting guide
- Production deployment guide

**Best for:** Comprehensive reference

### `docs/N8N_NOTIFICATIONS_STATUS.md` (10 minutes)

- Implementation status
- What's completed
- What's still needed
- Setup checklist
- Configuration reference
- Workflow structure

**Best for:** Understanding what's implemented

---

## 🔧 Scripts Reference

### `setup_n8n.sh` - Main Setup Script

```bash
bash scripts/setup_n8n.sh

# Does:
# ✅ Checks Docker installed
# ✅ Starts PostgreSQL
# ✅ Starts N8N instance
# ✅ Starts Backend service
# ✅ Shows next steps
```

### `import_n8n_workflow.sh` - Import Workflow

```bash
bash scripts/import_n8n_workflow.sh
# Or with custom URL:
bash scripts/import_n8n_workflow.sh http://n8n-prod.example.com
```

### `setup_telegram.sh` - Setup Telegram

```bash
bash scripts/setup_telegram.sh

# Interactive guide:
# 1. Walk through @BotFather steps
# 2. Get TELEGRAM_BOT_TOKEN
# 3. Get TELEGRAM_CHAT_ID
# 4. Auto-update .env
# 5. Restart backend
```

### `test_n8n_webhook.sh` - Test Webhook

```bash
bash scripts/test_n8n_webhook.sh

# Tests webhook with sample payload
# Shows response status
# Gives troubleshooting tips
```

### `show_n8n_summary.sh` - Quick Reference

```bash
bash scripts/show_n8n_summary.sh

# Displays visual quick reference
# Shows all scripts and URLs
# Provides example commands
```

---

## 🌐 Important URLs & Ports

| Service           | URL                                                   | Port | Purpose             |
| ----------------- | ----------------------------------------------------- | ---- | ------------------- |
| **N8N Dashboard** | http://localhost:5678                                 | 5678 | Admin workflows     |
| **Backend API**   | http://localhost:8001                                 | 8001 | REST API            |
| **Django Admin**  | http://localhost:8001/admin                           | 8001 | Database management |
| **PostgreSQL**    | localhost:5433                                        | 5433 | Database            |
| **N8N Webhook**   | http://localhost:5678/webhook/restaurant-admin-notify | 5678 | Receive bookings    |

---

## ⚙️ Key Configuration

### Required (.env variables)

```
N8N_ADMIN_NOTIFICATIONS_ENABLED=1
N8N_ADMIN_WEBHOOK_URL=http://localhost:5678/webhook/restaurant-admin-notify
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  ← GET FROM @BotFather
TELEGRAM_CHAT_ID=-123456789                                      ← GET FROM @userinfobot
```

### Workflow Components

- **Webhook Node**: Receives POST requests
- **Build Message Node**: Formats booking data
- **Secret Check Node**: Validates header
- **Telegram Node**: Sends to admin group
- **Facebook Node**: Optional notification

---

## 🧪 Testing Flow

```
Level 1: Webhook Test
  bash scripts/test_n8n_webhook.sh
  → Verifies N8N is responding

Level 2: N8N Execution Test
  → Check N8N Dashboard → Executions
  → Verify workflow executes

Level 3: End-to-End Test
  → Create booking in Django Admin
  → Check Telegram receives message
  → Verify complete flow
```

---

## 🐛 Common Issues Quick Fix

| Issue               | Check               | Fix                            |
| ------------------- | ------------------- | ------------------------------ |
| N8N not accessible  | `docker-compose ps` | `docker-compose restart n8n`   |
| Webhook 401         | Secret matches      | Update `.env`, restart backend |
| No Telegram msg     | Bot token valid     | Run `setup_telegram.sh`        |
| Workflow missing    | Import status       | Run `import_n8n_workflow.sh`   |
| Backend won't start | Logs                | `docker-compose logs backend`  |

---

## ✅ Setup Verification

- [ ] Docker running: `docker-compose ps`
- [ ] N8N accessible: http://localhost:5678
- [ ] Admin account created in N8N
- [ ] Workflow imported: Dashboard shows "Restaurant Admin Notifications"
- [ ] Telegram bot token set in `.env`
- [ ] Telegram chat ID set in `.env`
- [ ] Backend restarted: `docker-compose restart backend`
- [ ] Webhook test passes: `bash scripts/test_n8n_webhook.sh`
- [ ] Test booking created
- [ ] Telegram notification received ✅

---

## 🎯 Usage After Setup

Once setup complete:

1. **Create Booking**
   - Django Admin or API
   - Django signal fires automatically

2. **Webhook Sent**
   - Backend sends HTTP POST to N8N
   - Includes booking details

3. **N8N Processes**
   - Validates secret header
   - Formats message
   - Sends to Telegram

4. **Admin Receives**
   - Notification in Telegram
   - All booking details included

---

## 📚 Learning Resources

- **N8N Official Docs**: https://docs.n8n.io/
- **N8N Webhook Guide**: https://docs.n8n.io/workflows/triggers/webhook/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Docker Documentation**: https://docs.docker.com/

---

## 🚀 Production Deployment Tips

1. Use HTTPS for webhook URL
2. Set strong webhook secret
3. Setup N8N authentication
4. Monitor webhook delivery
5. Use database backups
6. Configure rate limiting
7. Setup alerting
8. Use managed N8N service (optional)

---

## 📞 Need Help?

1. **Quick questions?** → Read relevant `.md` file
2. **Setup issues?** → Run `bash scripts/show_n8n_summary.sh`
3. **Webhook problems?** → Check `docs/N8N_HOW_TO_RUN.md` Troubleshooting
4. **Telegram issues?** → Run `bash scripts/setup_telegram.sh` again
5. **Still stuck?** → Check logs: `docker-compose logs`

---

## 📋 Files at a Glance

| File                             | Size  | Purpose        | Read Time |
| -------------------------------- | ----- | -------------- | --------- |
| N8N_QUICKSTART.md                | 10KB  | Quick start    | 5 min     |
| N8N_COMPLETE_GUIDE.md            | 15KB  | Complete guide | 15 min    |
| docs/N8N_HOW_TO_RUN.md           | 12KB  | How to run     | 20 min    |
| docs/N8N_SETUP_GUIDE.md          | 18KB  | Full setup     | 30 min    |
| docs/N8N_NOTIFICATIONS_STATUS.md | 14KB  | Status         | 10 min    |
| Total Documentation              | ~70KB | All guides     | 90 min    |

---

## ✨ What You Get

✅ **Complete Setup**

- N8N instance ready to run
- Workflow pre-configured
- Backend fully integrated
- Docker Compose ready

✅ **Multiple Setup Methods**

- Automatic (1 script)
- Manual step-by-step
- Customizable URLs
- Option for Telegram/Facebook

✅ **Comprehensive Documentation**

- 5 detailed guides
- Quick references
- Troubleshooting
- Testing procedures

✅ **Automation Scripts**

- Setup automation
- Workflow import
- Testing utilities
- Configuration helpers

✅ **Production Ready**

- Error handling
- Security (secret validation)
- Logging & monitoring
- Extensible architecture

---

## 🎉 Ready?

```bash
# Start here
bash scripts/setup_n8n.sh

# Then follow the prompts!
```

**Everything is ready. You just need to run one script.** 🚀

---

## 📞 Quick Reference Card

```
DOCUMENTATION:
  Quick? → N8N_QUICKSTART.md
  Complete? → N8N_COMPLETE_GUIDE.md
  Full? → docs/N8N_SETUP_GUIDE.md

SCRIPTS:
  Setup: bash scripts/setup_n8n.sh
  Import: bash scripts/import_n8n_workflow.sh
  Telegram: bash scripts/setup_telegram.sh
  Test: bash scripts/test_n8n_webhook.sh

URLs:
  N8N: http://localhost:5678
  Backend: http://localhost:8001
  Admin: http://localhost:8001/admin

TIMES:
  5 min: N8N_QUICKSTART.md
  10 min: Run setup_n8n.sh
  5 min: Setup Telegram
  5 min: Test webhook
  Total: 25 minutes to full setup ✅
```

---

**Maintained by**: Development Team  
**Last Updated**: June 14, 2026  
**Status**: ✅ Production Ready
