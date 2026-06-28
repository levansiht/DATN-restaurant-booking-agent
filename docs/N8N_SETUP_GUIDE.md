# N8N Setup & Workflow Import - Hướng Dẫn Chi Tiết

**Ngày tạo**: June 14, 2026

---

## 🚀 Option 1: Chạy N8N qua Docker Compose (Khuyên dùng)

### 1.1 Tự động (Docker Compose đã setup)

Project đã có N8N trong `backend/docker-compose.yml`:

```bash
cd /home/levansy/DATN/demo-chat-bot/backend

# Start tất cả services (PostgreSQL + Backend + N8N)
docker-compose up -d

# Kiểm tra N8N chạy chưa
docker-compose logs n8n | tail -20

# Check services status
docker-compose ps
```

**Expected output:**

```
CONTAINER ID   STATUS              PORTS
...
ai_chat_bot_n8n       Up 2 minutes   0.0.0.0:5678->5678/tcp
ai_chat_bot_backend   Up 1 minute    0.0.0.0:8001->8000/tcp
ai_chat_bot_db        Up 3 minutes   0.0.0.0:5433->5432/tcp
```

### 1.2 Sau khi N8N chạy

Truy cập: **http://localhost:5678**

**Lần đầu tiên:**

- Sẽ yêu cầu tạo tài khoản admin
- Điền email/password
- Login vào dashboard

---

## 📥 Step 2: Import Workflow

### 2.1 Cách 1: Import từ File JSON

**Bước 1:** Trên N8N dashboard, click "New Workflow"

```
Left sidebar → "Workflows" → "+ New Workflow"
```

**Bước 2:** Click menu icon (⋯) → "Import from file"

```
Top menu → "..." (menu) → "Import from file"
```

**Bước 3:** Select file

```
Chọn: /home/levansy/DATN/demo-chat-bot/docs/n8n/restaurant-admin-notifications.workflow.json
```

**Bước 4:** Import thành công

```
Sẽ hiển thị workflow với 5 nodes:
- Webhook (Admin Notification Webhook)
- BuildMessage (Build Message)
- CheckSecret (Secret OK?)
- Telegram (Telegram sender)
- Facebook (Facebook Messenger sender)
```

### 2.2 Cách 2: Import qua API (Script)

Tạo file `/home/levansy/DATN/demo-chat-bot/scripts/import_n8n_workflow.sh`:

```bash
#!/bin/bash

# Variables
N8N_URL="http://localhost:5678"
WORKFLOW_FILE="/home/levansy/DATN/demo-chat-bot/docs/n8n/restaurant-admin-notifications.workflow.json"

# Get auth token (nếu cần - tùy N8N version)
# TOKEN=$(curl -s -X POST $N8N_URL/api/v1/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"password"}' | jq -r '.token')

# Import workflow
curl -X POST "$N8N_URL/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d @$WORKFLOW_FILE

echo "✅ Workflow imported successfully!"
```

**Chạy script:**

```bash
chmod +x /home/levansy/DATN/demo-chat-bot/scripts/import_n8n_workflow.sh
bash /home/levansy/DATN/demo-chat-bot/scripts/import_n8n_workflow.sh
```

### 2.3 Cách 3: Copy-Paste (Dễ nhất)

**Bước 1:** Mở workflow JSON

```bash
cat /home/levansy/DATN/demo-chat-bot/docs/n8n/restaurant-admin-notifications.workflow.json
```

**Bước 2:** Trên N8N dashboard

```
Click "..." menu → "Import from JSON"
Paste entire JSON content → Click "Import"
```

---

## ⚙️ Step 3: Cấu Hình Environment Variables trong N8N

N8N cần biết các credentials để gửi Telegram/Facebook.

### 3.1 Qua Docker Environment

Nếu dùng Docker Compose, edit `backend/docker-compose.yml`:

```yaml
n8n:
  image: n8nio/n8n:latest
  container_name: ai_chat_bot_n8n
  ports:
    - 5678:5678
  environment:
    - N8N_HOST=localhost
    - N8N_PORT=5678
    - N8N_PROTOCOL=http
    - WEBHOOK_URL=http://localhost:5678/
    - GENERIC_TIMEZONE=Asia/Bangkok
    - TZ=Asia/Bangkok
    # 👇 N8N Secret (phải match với backend .env)
    - N8N_ADMIN_WEBHOOK_SECRET=${N8N_ADMIN_WEBHOOK_SECRET:-change-this-n8n-secret}
    # 👇 Telegram Credentials
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
    - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}
    # 👇 Facebook (optional)
    - FACEBOOK_PAGE_ACCESS_TOKEN=${FACEBOOK_PAGE_ACCESS_TOKEN:-}
    - FACEBOOK_ADMIN_PSID=${FACEBOOK_ADMIN_PSID:-}
```

**Cập nhật `.env` file:**

```bash
# backend/.env
N8N_ADMIN_WEBHOOK_SECRET=change-this-n8n-secret
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_ADMIN_PSID=
```

**Restart containers:**

```bash
docker-compose down
docker-compose up -d
```

### 3.2 Qua N8N UI (Credentials)

**Bước 1:** Login N8N → Settings → Credentials

```
http://localhost:5678
Click: Settings icon (⚙️) → Credentials
```

**Bước 2:** Tạo Telegram credential

```
Click "+ Create New Credential"
Chọn "Telegram"
Điền:
  - Bot Token: [TELEGRAM_BOT_TOKEN]
  - Chat ID: [TELEGRAM_CHAT_ID]
Click "Create"
```

**Bước 3:** Update workflow nodes

```
Mở workflow → Click "Telegram" node
Chọn credential vừa tạo từ dropdown
Click "Execute Node" để test
```

---

## 🧪 Step 4: Test Workflow

### 4.1 Test Webhook

**Cách 1: Curl từ Terminal**

```bash
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "Content-Type: application/json" \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -d '{
    "event": "booking.created",
    "action": "created",
    "previous_status": null,
    "restaurant": {
      "name": "PSCD Japanese Dining",
      "website_url": "http://localhost:5173"
    },
    "booking": {
      "id": 1,
      "code": "BK001",
      "status": "pending",
      "status_label": "Pending",
      "source": "web",
      "guest_name": "Nguyễn Văn A",
      "guest_phone": "0901234567",
      "guest_email": "customer@example.com",
      "booking_date": "2026-06-15",
      "booking_time": "19:00",
      "party_size": 4,
      "notes": "Window seat preferred",
      "table": {
        "id": 1,
        "floor": 1,
        "capacity": 4,
        "table_type": "4_seater",
        "table_type_label": "4-seat table"
      }
    },
    "payment": null
  }'

# Expected response:
# {"ok": true, "text": "[ADMIN] booking.created (created)..."}
```

**Cách 2: N8N UI Test**

```
Dashboard → Workflows → restaurant-admin-notifications
Click "Webhook" node → Click "Execute Node"
N8N sẽ generate sample payload
```

### 4.2 Monitor Workflow Execution

```
N8N Dashboard → "Executions" tab
Sẽ hiển thị log của mỗi request:
- ✅ Status (Success/Failed)
- ⏱️ Duration
- 📊 Nodes execution history
```

### 4.3 Debug Issues

**Kiểm tra logs:**

```bash
# N8N logs
docker-compose logs n8n -f

# Backend logs
docker-compose logs backend -f
```

**Nếu webhook fail:**

- Kiểm tra secret header match (`X-N8N-Secret`)
- Kiểm tra webhook URL đúng
- Kiểm tra N8N instance running (`docker-compose ps`)

---

## 📱 Step 5: Cấu Hình Telegram Bot

### 5.1 Tạo Telegram Bot

**Bước 1:** Chat với @BotFather trên Telegram

```
Telegram → Search "BotFather" → Start
Command: /newbot
BotFather hỏi:
  - Đặt tên: "PSCD Admin Notifications"
  - Đặt username: "pscd_restaurant_bot" (phải unique, kết thúc bằng _bot)
```

**Bước 2:** Copy Token

```
BotFather sẽ gửi:
"Use this token to access the HTTP API:
xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

Paste vào TELEGRAM_BOT_TOKEN
```

### 5.2 Lấy Chat ID

**Cách 1: Chat với bot**

```
1. Chat: /start tới bot vừa tạo
2. Chat: /getme tới @userinfobot
3. Copy ID hiển thị
4. Paste vào TELEGRAM_CHAT_ID
```

**Cách 2: Tạo Group**

```
1. Tạo private Telegram group
2. Add bot vào group
3. Chat /id tới @userinfobot trong group
4. Copy group ID (negative number, vd: -123456789)
```

### 5.3 Update .env

```bash
# backend/.env
TELEGRAM_BOT_TOKEN=xxxxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-123456789
```

**Restart backend:**

```bash
docker-compose restart backend
```

---

## 📊 Step 6: End-to-End Test

### 6.1 Tạo Booking Test

**Option 1: Django Admin**

```bash
# Vào Django admin
http://localhost:8001/admin

# Login (tạo superuser nếu chưa)
python manage.py createsuperuser

# Tạo booking:
Restaurant Booking → Bookings → Add Booking
- Guest name: "Test User"
- Guest phone: "0901234567"
- Booking date: "2026-06-15"
- Booking time: "19:00"
- Party size: 2
- Status: "pending"
- Click Save
```

**Option 2: API Call**

```bash
# Create booking via API
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

### 6.2 Kiểm Tra Telegram Notification

```
✅ Nên nhận tin nhắn trên Telegram:

[ADMIN] booking.created (created)
Mã booking: BK001
Khách: Test User - 0901234567
Thời gian: 2026-06-15 19:00
Số khách: 2
Bàn: 1 - tầng 1 - 4-seat table
Trạng thái booking: pending
Thanh toán: N/A
```

### 6.3 Monitor Workflow

```
N8N Dashboard → Executions
Sẽ thấy execution history:
1. Webhook received ✅
2. BuildMessage executed ✅
3. CheckSecret validated ✅
4. Telegram sent ✅
```

---

## 🔧 Troubleshooting

### Issue 1: N8N không chạy

```bash
# Check logs
docker-compose logs n8n

# Common issues:
- Port 5678 đang bị dùng
- N8N volume permissions

# Fix:
docker-compose down
docker-compose rm -f n8n
docker-compose up -d n8n
```

### Issue 2: Webhook không response

```bash
# Kiểm tra secret
echo $N8N_ADMIN_WEBHOOK_SECRET

# Verify format
curl -v http://localhost:5678/webhook/restaurant-admin-notify

# Check N8N logs
docker-compose logs n8n | grep -i webhook
```

### Issue 3: Telegram message không gửi

```bash
# Verify bot token
curl -s -X GET https://api.telegram.org/botTOKEN/getMe | jq .

# Check if bot is in group
# Kiểm tra Group ID (phải negative cho group)

# Test send direct
curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
  -d "chat_id=-123456789&text=Test"
```

### Issue 4: N8N credential không save

```bash
# N8N data persistence (docker-compose)
volumes:
  - n8n_data:/home/node/.n8n

# Check volume
docker volume ls | grep n8n
```

---

## 📋 Quick Start Checklist

- [ ] **Bước 1:** Chạy Docker Compose

  ```bash
  cd backend && docker-compose up -d
  ```

- [ ] **Bước 2:** Truy cập N8N

  ```
  http://localhost:5678 → Create admin account
  ```

- [ ] **Bước 3:** Import workflow

  ```
  Workflows → "..." → "Import from file"
  Select: docs/n8n/restaurant-admin-notifications.workflow.json
  ```

- [ ] **Bước 4:** Cấu hình Telegram

  ```
  1. Chat @BotFather → /newbot → Get TOKEN
  2. Chat @userinfobot → Get CHAT_ID
  3. Update backend/.env:
     TELEGRAM_BOT_TOKEN=xxx
     TELEGRAM_CHAT_ID=-xxx
  4. Restart: docker-compose restart backend
  ```

- [ ] **Bước 5:** Test webhook

  ```bash
  curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
    -H "X-N8N-Secret: change-this-n8n-secret" \
    -H "Content-Type: application/json" \
    -d '{"event":"booking.created","booking":{"id":1,"code":"BK001","guest_name":"Test"}}'
  ```

- [ ] **Bước 6:** Test thực tế
  ```
  Tạo booking → Check Telegram notification
  ```

---

## 📞 Support Links

- **N8N Documentation**: https://docs.n8n.io/
- **N8N Webhook**: https://docs.n8n.io/workflows/triggers/webhook/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Docker Compose**: https://docs.docker.com/compose/

---

## 📝 Notes

- N8N workflow chạy **stateless** - mỗi webhook request độc lập
- Telegram credentials cần **valid** - nếu bot token sai, sẽ fail silently
- Webhook secret **bắt buộc** - match giữa backend & N8N
- Database credentials **tự động share** via docker network
