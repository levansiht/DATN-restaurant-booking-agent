# 🤖 N8N Setup Keys cho Telegram & Facebook

**Cập nhật**: June 23, 2026  
**Mục đích**: Hướng dẫn setup Telegram Bot & Facebook Page để gửi messages qua N8N

---

## 📱 PHẦN 1: SETUP TELEGRAM BOT

### 1.1 Tạo Telegram Bot (Get Token)

**Bước 1:** Mở Telegram → Search "BotFather"

```
1. Mở Telegram app/web
2. Search: @BotFather
3. Click vào kết quả
4. Click "Start" button
```

**Bước 2:** Tạo Bot mới

```
Type lệnh: /newbot
BotFather sẽ hỏi:
  ├─ "Alright! A new bot. How are we going to call it?
     Please choose a name for your bot."
  ├─ Type: "PSCD Admin Notifications" (tên display)
  │
  └─ "Good. Now let's choose a username for your bot.
     It must end in `bot`. Ex: TetrisBot or tetris_bot."
     Type: "pscd_restaurant_bot" (phải unique & kết thúc _bot)
```

**Bước 3:** Copy Token

```
BotFather sẽ trả lời:
"Done! Congratulations on your new bot.
You'll find it at https://t.me/pscd_restaurant_bot.
You can now add a description, about section and profile picture for your bot,
see /help for a list of commands. By the way, when you've finished creating
your cool bot, ping our bot Support if you want a better username for the
bot. Just make sure the bot is cool enough. We're looking forward to it!

Use this token to access the HTTP API:
👉 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi 👈

Keep your token secure and store it safely,
it can be used by anyone to control your bot."

✅ COPY token: 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
```

**Save lại:**

```bash
TELEGRAM_BOT_TOKEN="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
```

### 1.2 Lấy Telegram Chat ID

**Cách 1: Từ cá nhân (Private Chat)**

```
1. Chat với @userinfobot trên Telegram
2. @userinfobot sẽ reply:
   ├─ User ID: 123456789
   ├─ First Name: Your Name
   ├─ Username: @yourname
   └─ ...
3. Copy User ID: 123456789
```

**Save lại:**

```bash
TELEGRAM_CHAT_ID="123456789"
```

**Cách 2: Từ Group (Nên dùng cho Admin Notifications)**

```
1. Tạo Telegram group private: "PSCD Admin Notifications"
2. Add bot: @pscd_restaurant_bot vào group
3. Send message vào group
4. Chat /id tới @userinfobot
5. @userinfobot sẽ reply với Group ID (số âm): -123456789
```

**Save lại:**

```bash
TELEGRAM_CHAT_ID="-123456789"  # Negative number cho group
```

### 1.3 Update Backend .env

**Mở file:**

```bash
nano /home/levansy/DATN/demo-chat-bot/backend/.env
```

**Tìm và update:**

```bash
# 🔔 TELEGRAM CONFIGURATION
TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
TELEGRAM_CHAT_ID=-123456789
```

**Save:** `Ctrl+X` → `Y` → `Enter`

### 1.4 Verify Telegram Bot Working

**Test trực tiếp qua Telegram Bot API:**

```bash
# Test bot token
curl -s -X GET "https://api.telegram.org/bot123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi/getMe" | jq .

# Expected response:
# {
#   "ok": true,
#   "result": {
#     "id": 123456789,
#     "is_bot": true,
#     "first_name": "PSCD Admin Notifications",
#     "username": "pscd_restaurant_bot",
#     ...
#   }
# }
```

**Test gửi message:**

```bash
curl -X POST "https://api.telegram.org/bot123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi/sendMessage" \
  -d "chat_id=-123456789" \
  -d "text=🤖 Test message from N8N"

# Expected response:
# {"ok":true,"result":{"message_id":123,...}}
```

**Nếu nhận được message trên Telegram → ✅ Bot working!**

---

## 💬 PHẦN 2: SETUP FACEBOOK MESSENGER

### 2.1 Tạo Facebook Page (nếu chưa có)

**Bước 1:** Truy cập Facebook Business Manager

```
1. Mở: https://business.facebook.com/
2. Login with your Facebook account
3. Chọn hoặc tạo Business account
```

**Bước 2:** Tạo hoặc chọn Page

```
1. Left sidebar → Pages
2. Chọn page hoặc click "Create new page"
3. Nếu tạo mới:
   ├─ Category: "Restaurant/Café"
   ├─ Page Name: "PSCD Japanese Dining"
   ├─ Click "Create Page"
```

### 2.2 Tạo Facebook App (Get Access Token)

**Bước 1:** Tạo App

```
1. Truy cập: https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Chọn "Consumer" type
4. Điền:
   ├─ App Name: "PSCD Admin Notifications"
   ├─ App Contact Email: your-email@gmail.com
   ├─ App Purpose: "Admin notifications & customer engagement"
5. Click "Create App"
```

**Bước 2:** Thêm Messenger Product

```
1. Trên App Dashboard, tìm "Messenger"
2. Click "Set Up"
3. Click "Continue"
```

**Bước 3:** Tạo Access Token

```
1. Trong Messenger settings:
   ├─ "Access Tokens" section
   ├─ Click "Add" hoặc "Generate Token"
2. Chọn Facebook Page: "PSCD Japanese Dining"
3. Chấp nhận permissions
4. Copy Token: 👉 EAABSM... 👈
```

**Save lại:**

```bash
FACEBOOK_PAGE_ACCESS_TOKEN="EAABSMxxxxxxxxxxxxxx"
```

### 2.3 Lấy Facebook Admin PSID (Personal ID)

**PSID là ID của người nhận messages**

**Cách 1: Qua Webhook (Khi khách chat tới page)**

```
Khi khách gửi message tới page:
{
  "sender": {
    "id": "1234567890"  👈 PSID của khách
  },
  ...
}
```

**Cách 2: Get Your Own PSID**

```bash
# Sử dụng Facebook Graph API
curl -X GET "https://graph.instagram.com/me?access_token=YOUR_TOKEN"

# Hoặc qua dashboard:
1. Vào page conversation
2. Kiểm tra message thread
3. PSID nằm trong webhook payload
```

**Save lại:**

```bash
FACEBOOK_ADMIN_PSID="1234567890"
```

### 2.4 Update Backend .env

**Mở file:**

```bash
nano /home/levansy/DATN/demo-chat-bot/backend/.env
```

**Tìm và update:**

```bash
# 💬 FACEBOOK CONFIGURATION
FACEBOOK_PAGE_ACCESS_TOKEN=EAABSMxxxxxxxxxxxxxx
FACEBOOK_ADMIN_PSID=1234567890
```

**Save:** `Ctrl+X` → `Y` → `Enter`

### 2.5 Verify Facebook Access Token

**Test token:**

```bash
curl -X GET "https://graph.facebook.com/me?access_token=EAABSMxxxxxxxxxxxxxx"

# Expected response:
# {
#   "name": "PSCD Admin Notifications",
#   "id": "100087654321"
# }
```

**Test gửi message:**

```bash
curl -X POST "https://graph.facebook.com/v18.0/me/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": {"id": "1234567890"},
    "message": {"text": "🤖 Test message from N8N"},
    "access_token": "EAABSMxxxxxxxxxxxxxx"
  }'

# Expected response:
# {"recipient_id":"1234567890","message_id":"m_..."}
```

**Nếu thấy message trong Facebook Messenger → ✅ Token working!**

---

## ⚙️ PHẦN 3: SETUP CREDENTIALS TRONG N8N UI

### 3.1 Truy Cập N8N Credentials

**Bước 1:** Mở N8N

```
1. Truy cập: http://localhost:5678
2. Login with admin account
3. Click icon bánh răng ⚙️ (top right)
4. Click "Credentials"
```

**Bước 2:** Giao diện Credentials

```
Sẽ thấy:
├─ "Credentials" tab
├─ "New" button (để tạo mới)
└─ List credentials hiện có
```

### 3.2 Tạo Telegram Credential

**Cách 1: Qua UI (Nếu có Telegram node)**

```
1. Click "+ New" button
2. Search: "Telegram"
3. Nếu không thấy → Phải cài plugin
   (Telegram node có sẵn trong N8N)
4. Chọn "Telegram" type
5. Điền:
   ├─ Bot Token: 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
   └─ Click "Test connection"
6. Nếu test OK → Click "Save"
```

**Cách 2: Import/Paste JSON**

Nếu không thấy Telegram trong dropdown:

```
1. Click "Create New Credential"
2. Click "Edit as JSON"
3. Paste:
{
  "type": "telegram",
  "name": "Telegram Admin Bot",
  "data": {
    "botToken": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
  }
}
4. Click "Save"
```

### 3.3 Tạo Facebook Credential

```
1. Click "+ New" button
2. Search: "Facebook"
3. Chọn "Facebook Messenger"
4. Điền:
   ├─ Access Token: EAABSMxxxxxxxxxxxxxx
   └─ Click "Test connection"
5. Click "Save"
```

### 3.4 Dùng Credentials trong Workflow

**Nếu dùng Telegram Node:**

```
1. Mở Workflow
2. Add node: "Telegram"
3. Click "Credentials dropdown"
4. Chọn: "Telegram Admin Bot" (credential vừa tạo)
5. Điền Chat ID: -123456789
6. Click "Execute Node" để test
```

**Nếu dùng API HTTP (hiện tại):**

```
Workflow đang dùng:
- HTTP Request node
- Gọi: https://api.telegram.org/bot{token}/sendMessage
- Dùng environment variables: $env.TELEGRAM_BOT_TOKEN

Không cần credentials node, vì đã dùng API call.
```

---

## 🔄 PHẦN 4: RESTART & TEST

### 4.1 Restart Services

```bash
cd /home/levansy/DATN/demo-chat-bot/backend

# Restart backend (load new .env)
docker-compose restart backend

# Restart N8N (nếu cần)
docker-compose restart n8n

# Check logs
docker-compose logs -f backend
```

### 4.2 Test End-to-End

**Cách 1: Webhook Test qua Curl**

```bash
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "Content-Type: application/json" \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  -d '{
    "event": "booking.created",
    "action": "created",
    "booking": {
      "id": 1,
      "code": "TEST001",
      "guest_name": "Test User",
      "guest_phone": "0901234567",
      "booking_date": "2026-06-25",
      "booking_time": "19:00",
      "party_size": 4,
      "status": "pending",
      "status_label": "Chờ xác nhận"
    },
    "table": {
      "id": 1,
      "floor": 1,
      "capacity": 4,
      "table_type_label": "4-seater"
    }
  }'
```

**Expected response:**

```json
{
  "ok": true,
  "text": "[ADMIN] booking.created (created)\nMã booking: TEST001\n..."
}
```

**Bước 2:** Check Telegram notification

```
✅ Nên nhận message trên Telegram:
[ADMIN] booking.created (created)
Mã booking: TEST001
Khách: Test User - 0901234567
...
```

**Bước 3:** Check Facebook (nếu cài)

```
✅ Nên nhận message trên Facebook Messenger
```

### 4.3 Monitor Execution

**N8N Dashboard:**

```
1. Mở: http://localhost:5678
2. Click Workflow: "Restaurant Admin Notifications"
3. Click "Executions" tab
4. Sẽ thấy log của request:
   ├─ ✅ Webhook node: executed
   ├─ ✅ BuildMessage node: executed
   ├─ ✅ CheckSecret node: passed
   ├─ ✅ HTTP Telegram: sent
   └─ ✅ HTTP Facebook: sent (nếu cài)
```

---

## 🧪 PHẦN 5: TROUBLESHOOTING

### Issue 1: Telegram message không gửi đi

**Kiểm tra:**

```bash
# 1. Verify token format
echo $TELEGRAM_BOT_TOKEN

# 2. Test token directly
curl -s -X GET "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe" | jq .

# 3. Check chat ID (phải là negative cho group)
echo $TELEGRAM_CHAT_ID
```

**Fixes:**

```bash
# Nếu token sai → Update .env và restart
docker-compose restart backend

# Nếu chat ID sai:
# 1. Verify bot ở trong group
# 2. Chat /id tới @userinfobot
# 3. Copy negative ID: -123456789
# 4. Update .env
```

### Issue 2: Facebook message không gửi

**Kiểm tra:**

```bash
# Test access token
curl -X GET "https://graph.facebook.com/me?access_token=$FACEBOOK_PAGE_ACCESS_TOKEN"

# Test send message
curl -X POST "https://graph.facebook.com/v18.0/me/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": {"id": "'$FACEBOOK_ADMIN_PSID'"},
    "message": {"text": "Test"},
    "access_token": "'$FACEBOOK_PAGE_ACCESS_TOKEN'"
  }'
```

**Fixes:**

- Token expired → Refresh từ Facebook App Dashboard
- PSID sai → Verify ID từ conversation thread
- Permissions không đủ → Check app permissions trong Messenger settings

### Issue 3: N8N webhook không response

**Kiểm tra:**

```bash
# 1. N8N running?
docker-compose ps | grep n8n

# 2. Webhook URL format đúng?
# Phải là: http://localhost:5678/webhook/restaurant-admin-notify

# 3. Secret header match?
curl -X POST http://localhost:5678/webhook/restaurant-admin-notify \
  -H "X-N8N-Secret: change-this-n8n-secret" \
  ...

# 4. Check logs
docker-compose logs n8n | tail -20
```

### Issue 4: .env variables không load

```bash
# Restart service để load lại
docker-compose down
docker-compose up -d backend

# Verify variables loaded
docker-compose exec backend printenv | grep TELEGRAM
```

---

## 📋 QUICK CHECKLIST

```
☐ Bước 1: Tạo Telegram Bot
  ☐ Chat @BotFather → /newbot
  ☐ Copy TELEGRAM_BOT_TOKEN

☐ Bước 2: Lấy Telegram Chat ID
  ☐ Tạo group hoặc lấy personal ID
  ☐ Copy TELEGRAM_CHAT_ID (negative cho group)

☐ Bước 3: Setup Facebook (Optional)
  ☐ Tạo/chọn Facebook Page
  ☐ Tạo Facebook App
  ☐ Get FACEBOOK_PAGE_ACCESS_TOKEN
  ☐ Get FACEBOOK_ADMIN_PSID

☐ Bước 4: Update .env
  ☐ nano backend/.env
  ☐ TELEGRAM_BOT_TOKEN=xxx
  ☐ TELEGRAM_CHAT_ID=xxx
  ☐ FACEBOOK_PAGE_ACCESS_TOKEN=xxx (optional)
  ☐ FACEBOOK_ADMIN_PSID=xxx (optional)

☐ Bước 5: Restart & Test
  ☐ docker-compose restart backend
  ☐ curl test webhook
  ☐ Verify message trong Telegram/Facebook

☐ Bước 6: N8N Credentials (Optional)
  ☐ N8N Dashboard → Credentials
  ☐ Tạo Telegram credential
  ☐ Tạo Facebook credential
  ☐ Dùng trong workflow nodes
```

---

## 🔗 Useful Links

- **Telegram BotFather**: https://t.me/BotFather
- **Telegram UserInfoBot**: https://t.me/userinfobot
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Facebook Developers**: https://developers.facebook.com/
- **Facebook Messenger API**: https://developers.facebook.com/docs/messenger-platform/
- **N8N Telegram Node**: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram/
- **N8N HTTP Node**: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/

---

## 📝 Notes

- **Telegram token** nên keep private - không share public
- **Chat ID negative** để group, positive để personal
- **Facebook token** expire - refresh periodically từ app dashboard
- **N8N credentials** stored locally - backup lại thường xuyên
- Test qua API trước khi dùng trong workflow

---

**Status**: ✅ Ready to setup
**Last Updated**: June 23, 2026
