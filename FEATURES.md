# 🍽️ PSCD Restaurant Booking System - Tài liệu Chức năng

## 📋 Tổng quan Dự án

Hệ thống đặt bàn nhà hàng thông minh sử dụng AI Chatbot để tự động hóa quy trình đặt bàn, quản lý bàn và phục vụ khách hàng. Dự án được xây dựng với Django backend và React frontend.

---

## 🏗️ Kiến trúc Hệ thống

### Backend (Django + LangChain)

- **Framework**: Django REST Framework
- **Database**: PostgreSQL với pgvector extension
- **AI/ML**: LangChain, OpenAI GPT-4o-mini, Claude Sonnet
- **Authentication**: JWT (Simple JWT)

### Frontend (React + Vite)

- **Framework**: React 19 với Vite
- **Routing**: React Router DOM
- **UI Components**: Flowbite, Radix UI, Heroicons
- **Styling**: TailwindCSS

---

## 🎯 Chức năng Chính

### 1. 🤖 AI Chatbot Đặt Bàn Thông Minh

#### 1.1. Trò chuyện Tự nhiên

- **Xử lý ngôn ngữ tự nhiên**: Hiểu và phản hồi bằng tiếng Việt/tiếng Anh
- **Đa luồng hội thoại**: Theo dõi ngữ cảnh cuộc trò chuyện
- **Streaming response**: Phản hồi real-time cho trải nghiệm mượt mà
- **Personality**: Giọng điệu thân thiện, chuyên nghiệp như nhân viên thực thụ

#### 1.2. Trích xuất Thông tin Tự động (Entity Extraction)

- **Ngày đặt bàn**: Xử lý các biểu thức như "hôm nay", "ngày mai", "thứ 5 tuần sau"
- **Giờ đặt bàn**: Nhận diện giờ theo định dạng 24h hoặc 12h
- **Loại bàn**: Trong nhà, ngoài trời, phòng riêng, quầy bar, cửa sổ
- **Số lượng người**: Tự động nhận diện và validate
- **Thông tin khách**: Tên, số điện thoại
- **Yêu cầu đặc biệt**: Ghi chú về ăn chay, sinh nhật, dị ứng, v.v.

#### 1.3. Xử lý Thời gian Tiếng Việt (Vietnamese Time Processor)

```
Hỗ trợ các biểu thức:
- Ngày tương đối: "hôm nay", "hôm qua", "ngày mai"
- Thứ trong tuần: "thứ 2", "thứ ba", "chủ nhật"
- Tự động chuyển đổi sang định dạng YYYY-MM-DD
```

#### 1.4. Quy trình Đặt Bàn 4 Bước

**Bước 1: Thu thập thông tin cơ bản**

- Ngày, giờ, số lượng người
- Loại bàn ưa thích

**Bước 2: Tìm kiếm và gợi ý bàn**

- Kiểm tra bàn trống theo tiêu chí
- Gợi ý bàn phù hợp nhất
- Hiển thị thông tin chi tiết bàn

**Bước 3: Thu thập thông tin khách hàng**

- Tên khách hàng
- Số điện thoại liên hệ
- Ghi chú đặc biệt

**Bước 4: Xác nhận và hoàn tất**

- Tổng hợp thông tin đặt bàn
- Tạo mã booking code
- Gửi xác nhận cho khách

---

### 2. 🪑 Quản lý Bàn (Table Management)

#### 2.1. Thông tin Bàn

```python
- ID bàn: Mã định danh duy nhất
- Sức chứa: 1-20 người
- Loại bàn: INDOOR, OUTDOOR, PRIVATE, BAR, BOOTH, WINDOW
- Vị trí: Tầng 1, 2, 3
- Trạng thái: AVAILABLE, OCCUPIED, RESERVED, MAINTENANCE
- Kích thước: Chiều dài x chiều rộng
- Tiện nghi: Gần cửa sổ, ổ cắm điện, view đẹp
```

#### 2.2. Tính năng Quản lý

- **Xem danh sách bàn**: Phân chia theo tầng
- **Lọc bàn**: Theo loại, sức chứa, trạng thái
- **Kiểm tra bàn trống**: Theo ngày giờ cụ thể
- **Cập nhật trạng thái**: Real-time status update
- **Thống kê**: Số bàn trống/đã đặt theo khung giờ

#### 2.3. Table Tools cho AI Agent

```python
- get_available_tables(): Lấy danh sách bàn trống
- search_tables(): Tìm bàn theo tiêu chí
- get_table_info(): Xem chi tiết bàn
- check_availability(): Kiểm tra bàn có trống không
```

---

### 3. 📅 Quản lý Đặt Bàn (Booking Management)

#### 3.1. Thông tin Booking

```python
- Mã đặt bàn: Code 8 ký tự tự động
- Thông tin bàn: Table ID, loại bàn
- Thông tin khách: Tên, SĐT, email (optional)
- Thời gian: Ngày, giờ đặt bàn
- Số lượng: Party size
- Trạng thái: PENDING, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW
- Nguồn đặt: WEBSITE, PHONE, WALK_IN, MOBILE_APP, THIRD_PARTY
- Ghi chú: Yêu cầu đặc biệt
```

#### 3.2. Trạng thái Booking

- **PENDING**: Chờ xác nhận
- **CONFIRMED**: Đã xác nhận
- **CANCELLED**: Đã hủy
- **COMPLETED**: Hoàn thành
- **NO_SHOW**: Khách không đến

#### 3.3. Tính năng Booking

- ✅ Tạo booking mới
- ✅ Xác nhận booking
- ✅ Hủy booking
- ✅ Cập nhật thông tin
- ✅ Tìm kiếm booking theo mã/SĐT/tên
- ✅ Xem lịch sử booking
- ✅ Thống kê booking theo ngày/tuần/tháng

---

### 4. 🔍 Tìm kiếm và Tra cứu (Search & Query)

#### 4.1. Tìm kiếm Booking

```
GET /api/restaurant-booking/search/
Params:
  - code: Mã đặt bàn
  - phone: Số điện thoại
  - name: Tên khách hàng
  - date_from: Từ ngày
  - date_to: Đến ngày
  - status: Trạng thái
```

#### 4.2. Tìm kiếm Bàn

```
GET /api/restaurant-booking/tables/
Params:
  - date: Ngày cần kiểm tra
  - floor: Tầng
  - type: Loại bàn
  - capacity: Sức chứa
  - status: Trạng thái
```

#### 4.3. Thống kê và Báo cáo

- Tổng số booking theo ngày/tuần/tháng
- Tỷ lệ lấp đầy bàn
- Số booking theo trạng thái
- Top khung giờ đặt bàn
- Loại bàn được ưa chuộng

---

### 5. 💬 Giao diện Người dùng (UI/UX)

#### 5.1. Landing Page

- **Thông tin nhà hàng**: Tên, địa chỉ, giờ mở cửa
- **Highlights**: Đặc điểm nổi bật
- **Call-to-action**: Button "Đặt bàn ngay"

#### 5.2. Booking Interface

**Tab 1: Form đặt bàn thủ công**

- Chọn ngày (Date picker)
- Chọn giờ (Time picker)
- Chọn số người
- Chọn bàn từ sơ đồ

**Tab 2: Chat với AI**

- Giao diện chat messenger
- Typing indicator
- Streaming response
- History tracking

#### 5.3. Table Grid View

```
- Sơ đồ bàn theo tầng
- Màu sắc phân biệt trạng thái:
  ✅ Xanh lá: Có sẵn
  🟡 Vàng: Đã đặt
  🔴 Đỏ: Đang sử dụng
  ⚙️ Xám: Bảo trì
- Click chọn bàn
- Tooltip hiển thị thông tin
```

#### 5.4. Search Results Page

- Danh sách booking tìm được
- Chi tiết từng booking
- Actions: Xác nhận, Hủy, Xem chi tiết

---

### 6. 🔧 Tính năng Kỹ thuật (Technical Features)

#### 6.1. AI & Machine Learning

- **LangChain Integration**: Quản lý agents và tools
- **Multi-provider Support**: OpenAI GPT-4, Claude Anthropic
- **Streaming**: Server-Sent Events (SSE) cho real-time response
- **Context Management**: Conversation memory và history
- **Entity Extraction**: NER cho tiếng Việt

#### 6.2. Database

- **PostgreSQL**: Relational database
- **pgvector**: Vector similarity search
- **Soft Delete**: Giữ lại dữ liệu đã xóa
- **Timestamps**: Auto tracking created_at, updated_at
- **Indexing**: Tối ưu query performance

#### 6.3. API Design

- **RESTful API**: Chuẩn REST
- **Pagination**: Custom pagination
- **Filtering**: Django-filter integration
- **Serialization**: DRF serializers
- **Validation**: Request/Response validation
- **Documentation**: Swagger/OpenAPI (drf-spectacular)

#### 6.4. Security

- **CORS**: Configured cho frontend
- **CSRF**: Token protection
- **JWT**: Stateless authentication
- **Rate Limiting**: Throttling (100/hour anon, 1000/hour user)
- **Environment Variables**: Sensitive data protection

#### 6.5. Performance

- **Database Indexing**: Tối ưu query
- **Query Optimization**: Select/Prefetch related
- **Caching**: Response caching
- **Streaming**: Chunked response
- **Lazy Loading**: Frontend components

---

### 7. 🗂️ Cấu trúc Dữ liệu (Data Models)

#### 7.1. Table Model

```python
{
  id: Integer,
  capacity: Integer (1-20),
  table_type: Enum,
  floor: Integer,
  status: Enum,
  width: Decimal,
  height: Decimal,
  is_near_window: Boolean,
  has_power_outlet: Boolean,
  has_good_view: Boolean,
  description: Text,
  created_at: DateTime,
  updated_at: DateTime,
  is_deleted: Boolean
}
```

#### 7.2. Booking Model

```python
{
  id: Integer,
  code: String (8 chars, unique),
  table: ForeignKey,
  guest_name: String,
  guest_phone: String,
  guest_email: String,
  booking_date: Date,
  booking_time: Time,
  party_size: Integer,
  status: Enum,
  source: Enum,
  special_requests: Text,
  notes: Text,
  created_at: DateTime,
  updated_at: DateTime,
  is_deleted: Boolean
}
```

---

### 8. 📱 Tính năng Nâng cao (Advanced Features)

#### 8.1. Xử lý Ngôn ngữ Tự nhiên

- **Intent Recognition**: Nhận diện ý định người dùng
- **Slot Filling**: Điền thông tin từng bước
- **Context Awareness**: Hiểu ngữ cảnh hội thoại
- **Multilingual**: Hỗ trợ tiếng Việt và tiếng Anh

#### 8.2. Smart Recommendations

- Gợi ý bàn dựa trên sở thích
- Gợi ý khung giờ ít đông
- Gợi ý combo bàn cho nhóm lớn

#### 8.3. Validation & Error Handling

- **Validate ngày giờ**: Không cho đặt quá khứ
- **Validate sức chứa**: Phù hợp với số người
- **Validate trùng lặp**: Không đặt trùng thời gian
- **Error messages**: Thông báo lỗi rõ ràng bằng tiếng Việt

#### 8.4. Analytics & Insights

- Dashboard thống kê
- Biểu đồ booking trends
- Phân tích khách hàng
- Dự đoán nhu cầu đặt bàn

---

### 9. 🔌 API Endpoints

#### Booking APIs

```
POST   /api/restaurant-booking/chat/         - Chat với AI
GET    /api/restaurant-booking/tables/       - Lấy danh sách bàn
POST   /api/restaurant-booking/bookings/     - Tạo booking mới
GET    /api/restaurant-booking/bookings/{id} - Chi tiết booking
PUT    /api/restaurant-booking/bookings/{id} - Cập nhật booking
DELETE /api/restaurant-booking/bookings/{id} - Hủy booking
GET    /api/restaurant-booking/search/       - Tìm kiếm booking
```

#### Admin APIs

```
POST   /admin/                               - Django admin
GET    /api/schema/                          - API schema
GET    /api/                                 - Swagger UI
```

---

### 10. 🎨 UI Components

#### Frontend Components

```
RestaurantBooking.jsx      - Main booking page
BookingSearch.jsx          - Search bookings page
RestaurantLayout.jsx       - Layout wrapper
RestaurantLanding.jsx      - Landing page
RestaurantHeader.jsx       - Header component
BookingForm.jsx            - Manual booking form
TableGrid.jsx              - Table selection grid
BookingChatbot.jsx         - AI chat interface
BotMessage.jsx             - Bot message bubble
UserMessage.jsx            - User message bubble
Thinking.jsx               - Loading indicator
```

---

### 11. 🚀 Hướng dẫn Sử dụng

#### Đặt bàn qua Chat

1. Mở trang đặt bàn
2. Click tab "Chat với AI"
3. Nhập yêu cầu: "Tôi muốn đặt bàn cho 4 người vào tối mai"
4. AI sẽ hỏi thêm thông tin cần thiết
5. Xác nhận và nhận mã booking

#### Đặt bàn thủ công

1. Chọn ngày từ calendar
2. Chọn giờ từ dropdown
3. Nhập số người
4. Chọn bàn từ sơ đồ
5. Điền thông tin khách hàng
6. Submit và nhận mã booking

#### Tra cứu booking

1. Vào trang Search
2. Nhập mã booking hoặc SĐT
3. Xem chi tiết đặt bàn
4. Có thể hủy nếu cần

---

### 12. 📊 Thống kê Dự án

```
Backend:
- Models: 2 (Table, Booking)
- Views: 8 endpoints
- Serializers: 3
- AI Agents: 1 (RestaurantBookingAgent)
- Tools: 4 (table search/availability tools)
- Migrations: 5

Frontend:
- Pages: 2
- Components: 10+
- Routes: 3
- API calls: 5+

Tổng Lines of Code: ~3000+ lines
```

---

### 13. 🔮 Tính năng Tương lai (Roadmap)

- [ ] Email/SMS xác nhận tự động
- [ ] Thanh toán đặt cọc online
- [ ] Tích hợp Google Calendar
- [ ] QR code check-in
- [ ] Review & Rating system
- [ ] Loyalty program
- [ ] Mobile app (React Native)
- [ ] Multi-language support (English, Korean, Japanese)
- [ ] Voice booking (Speech-to-text)
- [ ] Photo gallery cho bàn

---

### 14. 🛠️ Tech Stack Summary

**Backend**

- Django 6.0
- Django REST Framework 3.16
- LangChain 0.3
- OpenAI API
- Anthropic Claude
- PostgreSQL
- pgvector
- Gunicorn

**Frontend**

- React 19
- Vite 7
- React Router DOM 7
- TailwindCSS 4
- Flowbite
- Axios
- Heroicons

**DevOps**

- Docker & Docker Compose
- Git
- Environment Variables

---

## 📝 Ghi chú

- Hệ thống đang ở giai đoạn MVP (Minimum Viable Product)
- Database đang sử dụng PostgreSQL với connection `localhost:5433`
- AI models: GPT-4o-mini (primary), Claude Sonnet (backup)
- Tất cả API đều hỗ trợ CORS cho frontend development

---

**Phiên bản**: 1.0.0  
**Cập nhật lần cuối**: 28/02/2026  
**Tác giả**: PSCD Development Team
