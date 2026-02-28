# 📋 KẾ HOẠCH TRIỂN KHAI - Restaurant Booking System

## User Auth | Admin Dashboard | Payment | Telegram Notifications

**Ngày tạo**: 28/02/2026  
**Phiên bản**: 1.0  
**Ước tính thời gian**: 9-12 tuần

---

## 🎯 MỤC TIÊU DỰ ÁN

Nâng cấp hệ thống đặt bàn hiện tại với 4 tính năng chính:

1. **🚀 Hybrid Booking Model** - Guest checkout + Member benefits (Guest-First)
2. **👤 Hệ thống Auth cho User** - Đăng ký, đăng nhập, quản lý booking cá nhân (Optional)
3. **💳 Tích hợp Thanh toán** - SePay và Cryptocurrency
4. **📱 Thông báo Telegram** - Tự động thông báo qua n8n khi có booking/thanh toán

---

## 🆕 HYBRID BOOKING STRATEGY

### Chiến lược: Guest-First + Member Benefits

**Mục tiêu:**

- ✅ **Maximize Conversion** - Khách book nhanh không cần account (10-14% conversion)
- ✅ **Build Loyalty** - Guest upgrade thành member (30% after 3 months)
- ✅ **Reduce Fraud** - Guest verification via email, member full trust
- ✅ **Track Data** - Member data = marketing + personalization

### Flow Diagram

```
┌─────────────────────────────────────────────────┐
│           KHI KHÁCH VÀO WEBSITE                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  🚀 ĐẶT BÀN NHANH     📱 ĐĂNG NHẬP   🔐 ĐĂNG KÍ │
│  (Guest Checkout)    (Member)       (New)    │
│       ↓                  ↓              ↓      │
│       └──────────────────┴──────────────┘      │
│                    ↓                           │
│          ┌─────────────────────┐              │
│          │  CHAT / FORM        │              │
│          │  - Chọn bàn         │              │
│          │  - Nhập thông tin   │              │
│          └────────────┬────────┘              │
│                       ↓                       │
│          ┌─────────────────────┐              │
│          │  THANH TOÁN         │              │
│          │ (SePay / Crypto)    │              │
│          └────────────┬────────┘              │
│                       ↓                       │
│          ┌─────────────────────┐              │
│          │✅ BOOKING OK        │              │
│          │CODE + Email/SMS     │              │
│          └─────────────────────┘              │
│                                               │
│  GUEST FEATURES (Limited)                     │
│  ❌ Hủy/Sửa online → Gọi hotline             │
│  ❌ Không lịch sử → Email receipt             │
│  ❌ Không loyalty → Một lần qua               │
│                                               │
│  MEMBER FEATURES (Full Access)                │
│  ✅ Hủy/Sửa online (< 24h trước)             │
│  ✅ Lịch sử bookings trong app                │
│  ✅ Loyalty points (5% mỗi booking)           │
│  ✅ Member perks & special offers             │
│  ✅ Auto-fill thông tin                       │
│                                               │
└─────────────────────────────────────────────────┘
```

### Key Metrics

| Metric                  | Guest | Member | Hybrid (Target) |
| ----------------------- | ----- | ------ | --------------- |
| **Conversion Rate**     | 8-12% | 2-4%   | **10-14%** ✅   |
| **Repeat Booking**      | 5%    | 60%    | **45%**         |
| **Fraud Risk**          | High  | Low    | Medium          |
| **LTV**                 | $50   | $500+  | **$300+**       |
| **Member Upgrade Rate** | -     | -      | **30%**         |

### Implementation Overview

```
PHASE 1: Hybrid Booking Core
├─ Guest checkout optimization
├─ Member optional auth
├─ Unified payment flow
└─ Guest verification email

PHASE 2: Member Benefits
├─ Loyalty points system
├─ Membership tiers (Silver/Gold/Platinum)
├─ Discount management
└─ Member dashboard

PHASE 3: Admin Panel
├─ Dashboard thống kê
├─ Booking management
├─ Member management
└─ Revenue analytics

PHASE 4: Payment Integration
├─ SePay integration
├─ Crypto payment
└─ Webhook handlers

PHASE 5: Telegram Notifications
├─ n8n workflows
├─ Bot commands
└─ Notification service
```

---

## 📊 PHÂN TÍCH HIỆN TRẠNG

### ✅ ĐÃ CÓ SẴN (Tận dụng được ngay)

#### Backend Authentication Infrastructure

```
✅ User Model với role: SUPER_ADMIN, ADMIN, USER
✅ JWT Authentication (Simple JWT)
✅ API Endpoints:
   - POST /api/auth/login
   - POST /api/auth/sign-up
   - POST /api/auth/token/refresh
   - POST /api/auth/verify-email
   - GET /api/account/me
   - PUT /api/account/update
   - POST /api/account/change-password

✅ Email Service (SMTP configured)
✅ Google OAuth2 Integration
✅ Token refresh mechanism
✅ Permission classes (IsAdmin)
✅ Role-based Django Admin backend
```

#### Frontend Auth Infrastructure

```
✅ Axios với JWT interceptor
✅ Token refresh tự động (401 handling)
✅ Auth API client (login, signup, token utilities)
✅ LocalStorage token management
```

#### Booking System

```
✅ Table Model (capacity, type, floor, status)
✅ Booking Model (guest info, date/time, code generation)
✅ AI Chatbot đặt bàn
✅ RESTful API endpoints
✅ Search và filter functionality
```

### ❌ CHƯA CÓ (Cần xây dựng)

```
❌ Frontend Auth Pages (Login, Register, Verify Email)
❌ Protected Routes với role guards
❌ Admin Dashboard UI
❌ User Dashboard (My Bookings)
❌ Payment Model & Integration
❌ Telegram Bot & n8n Workflows
❌ Webhook handlers cho payment
❌ Notification system
```

---

## 🏗️ KIẾN TRÚC GIẢI PHÁP

### 1. Phân tách User & Admin

#### 1.1 Database Schema Changes

**Migration 1: Update Booking Model**

```python
# File: backend/restaurant_booking/models/booking.py

# THÊM FIELD MỚI:
user = models.ForeignKey(
    'accounts.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='bookings',
    verbose_name="Người đặt bàn"
)

# NOTE: Giữ lại guest_name, guest_email, guest_phone
# để support cả guest booking (không đăng nhập)
```

**Migration 2: Add Admin Settings Model**

```python
# File: backend/restaurant_booking/models/restaurant_settings.py

class RestaurantSettings(models.Model):
    """Cấu hình nhà hàng cho admin"""

    # Thông tin cơ bản
    restaurant_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    address = models.TextField()

    # Cài đặt đặt bàn
    min_party_size = models.IntegerField(default=1)
    max_party_size = models.IntegerField(default=20)
    default_booking_duration = models.IntegerField(default=2)  # hours
    advance_booking_days = models.IntegerField(default=30)

    # Cài đặt thanh toán
    deposit_required = models.BooleanField(default=False)
    deposit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    min_deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=100000)

    # Giờ mở cửa
    opening_time = models.TimeField(default='10:00')
    closing_time = models.TimeField(default='22:00')

    class Meta:
        db_table = 'restaurant_settings'
```

#### 1.2 Backend API Endpoints

**File mới: `backend/restaurant_booking/views/admin_views.py`**

```python
# ADMIN-ONLY ENDPOINTS (Permission: IsAdminOrSuperAdmin)

class AdminBookingListView(APIView):
    """
    GET /api/admin/bookings/
    - List all bookings với pagination, filter, search
    - Filters: date_from, date_to, status, table_id, user_id
    - Search: guest_name, guest_phone, booking_code
    - Sort: created_at, booking_date, booking_time
    """

class AdminBookingDetailView(APIView):
    """
    GET/PUT/DELETE /api/admin/bookings/<id>/
    - Chi tiết booking
    - Cập nhật status, notes, table assignment
    - Xóa booking (soft delete)
    """

class AdminDashboardStatsView(APIView):
    """
    GET /api/admin/dashboard/stats/
    Response:
    {
        "today_bookings": 15,
        "pending_bookings": 5,
        "total_revenue_today": 5000000,
        "occupancy_rate": 75.5,
        "popular_time_slots": [...],
        "bookings_by_status": {...}
    }
    """
```

**File mới: `backend/restaurant_booking/views/user_views.py`**

```python
# USER-ONLY ENDPOINTS (Permission: IsAuthenticated)

class MyBookingsListView(APIView):
    """
    GET /api/my-bookings/
    - Lấy danh sách booking của user hiện tại
    - Filter: status, date_from, date_to
    - Sort: booking_date DESC
    """

class MyBookingCancelView(APIView):
    """
    POST /api/my-bookings/<id>/cancel/
    - User tự hủy booking của mình
    - Validation: chỉ hủy được nếu còn > 2 giờ trước booking_time
    """
```

**File: `backend/common/permissions/role_permissions.py`**

```python
from rest_framework import permissions

class IsAdminOrSuperAdmin(permissions.BasePermission):
    """Chỉ Admin và SuperAdmin"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'SUPER_ADMIN']
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """User chỉ truy cập booking của mình, Admin truy cập tất cả"""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['ADMIN', 'SUPER_ADMIN']:
            return True
        return obj.user == request.user
```

#### 1.3 Frontend Architecture

**Cấu trúc thư mục mới:**

```
frontend/src/
├── pages/
│   ├── Auth/
│   │   ├── Login.jsx                 # ✨ MỚI
│   │   ├── Register.jsx              # ✨ MỚI
│   │   ├── VerifyEmail.jsx           # ✨ MỚI
│   │   ├── ForgotPassword.jsx        # ✨ MỚI
│   │   └── ResetPassword.jsx         # ✨ MỚI
│   │
│   ├── User/
│   │   ├── UserLayout.jsx            # ✨ MỚI - Layout với sidebar
│   │   ├── UserDashboard.jsx         # ✨ MỚI - Tổng quan booking
│   │   ├── MyBookings.jsx            # ✨ MỚI - Danh sách booking
│   │   ├── BookingDetail.jsx         # ✨ MỚI - Chi tiết 1 booking
│   │   └── UserProfile.jsx           # ✨ MỚI - Thông tin cá nhân
│   │
│   ├── Admin/
│   │   ├── AdminLayout.jsx           # ✨ MỚI - Layout admin
│   │   ├── AdminDashboard.jsx        # ✨ MỚI - Dashboard thống kê
│   │   ├── AdminBookings.jsx         # ✨ MỚI - Quản lý booking
│   │   ├── AdminBookingDetail.jsx    # ✨ MỚI - Chi tiết booking
│   │   ├── AdminTables.jsx           # ✨ MỚI - Quản lý bàn
│   │   ├── AdminUsers.jsx            # ✨ MỚI - Quản lý user
│   │   └── AdminSettings.jsx         # ✨ MỚI - Cài đặt hệ thống
│   │
│   └── RestaurantBooking/            # ✅ GIỮ NGUYÊN (public booking)
│       ├── RestaurantBooking.jsx
│       └── BookingSearch.jsx
│
├── components/
│   ├── Auth/
│   │   ├── ProtectedRoute.jsx        # ✨ MỚI - Route guard
│   │   ├── LoginForm.jsx             # ✨ MỚI
│   │   └── RegisterForm.jsx          # ✨ MỚI
│   │
│   ├── Admin/
│   │   ├── AdminSidebar.jsx          # ✨ MỚI
│   │   ├── BookingTable.jsx          # ✨ MỚI - Data table
│   │   ├── BookingFilters.jsx        # ✨ MỚI
│   │   ├── StatsCard.jsx             # ✨ MỚI
│   │   ├── TableManager.jsx          # ✨ MỚI - CRUD bàn
│   │   └── UserTable.jsx             # ✨ MỚI
│   │
│   ├── User/
│   │   ├── UserSidebar.jsx           # ✨ MỚI
│   │   ├── BookingCard.jsx           # ✨ MỚI
│   │   ├── BookingHistory.jsx        # ✨ MỚI
│   │   └── ProfileForm.jsx           # ✨ MỚI
│   │
│   └── RestaurantBooking/            # ✅ GIỮ NGUYÊN
│
├── contexts/
│   └── AuthContext.jsx               # ✨ MỚI - Global auth state
│
└── api/
    ├── auth.js                       # ✅ ĐÃ CÓ - Cải tiến thêm
    ├── admin.js                      # ✨ MỚI
    └── user.js                       # ✨ MỚI
```

**File: `frontend/src/App.jsx` (CẬP NHẬT)**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/Auth/ProtectedRoute";

// Auth pages
import Login from "./pages/Auth/Login";
import Register from "./pages/Auth/Register";

// User pages
import UserLayout from "./pages/User/UserLayout";
import UserDashboard from "./pages/User/UserDashboard";
import MyBookings from "./pages/User/MyBookings";

// Admin pages
import AdminLayout from "./pages/Admin/AdminLayout";
import AdminDashboard from "./pages/Admin/AdminDashboard";
import AdminBookings from "./pages/Admin/AdminBookings";

// Public pages
import RestaurantBooking from "./pages/RestaurantBooking/RestaurantBooking";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<RestaurantBooking />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* User Protected Routes */}
          <Route
            path="/user"
            element={
              <ProtectedRoute allowedRoles={["USER", "ADMIN", "SUPER_ADMIN"]}>
                <UserLayout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<UserDashboard />} />
            <Route path="bookings" element={<MyBookings />} />
          </Route>

          {/* Admin Protected Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="bookings" element={<AdminBookings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

**File: `frontend/src/contexts/AuthContext.jsx` (MỚI)**

```jsx
import { createContext, useState, useEffect, useContext } from "react";
import { authAPI } from "../api/auth";
import { toast } from "react-toastify";

export const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = authAPI.getAuthToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);
    } catch (error) {
      authAPI.removeAuthToken();
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);
      authAPI.setAuthToken(response.access_token, response.refresh_token);
      setUser(response.user);
      setIsAuthenticated(true);
      toast.success("Đăng nhập thành công!");
      return response;
    } catch (error) {
      toast.error(error.response?.data?.message || "Đăng nhập thất bại");
      throw error;
    }
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
    setIsAuthenticated(false);
    toast.info("Đã đăng xuất");
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, isAuthenticated, login, logout }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
};
```

---

### 2. Payment Integration (SePay & Crypto)

#### 2.1 Database Schema

**File: `backend/restaurant_booking/models/payment.py` (MỚI)**

```python
from django.db import models
from common.models import DateTimeModel, SoftDeleteModel

class Payment(DateTimeModel, SoftDeleteModel):
    """Model thanh toán đặt bàn"""

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        PROCESSING = "PROCESSING", "Đang xử lý"
        COMPLETED = "COMPLETED", "Thành công"
        FAILED = "FAILED", "Thất bại"
        REFUNDED = "REFUNDED", "Đã hoàn tiền"
        EXPIRED = "EXPIRED", "Hết hạn"

    class PaymentMethod(models.TextChoices):
        SEPAY = "SEPAY", "SePay"
        CRYPTO_BTC = "CRYPTO_BTC", "Bitcoin"
        CRYPTO_ETH = "CRYPTO_ETH", "Ethereum"
        CRYPTO_USDT = "CRYPTO_USDT", "USDT"

    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='VND')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    provider_transaction_id = models.CharField(max_length=200, null=True, blank=True)

    payment_url = models.URLField(max_length=500, null=True, blank=True)
    crypto_address = models.CharField(max_length=200, null=True, blank=True)
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    payment_data = models.JSONField(default=dict, blank=True)
    webhook_data = models.JSONField(default=dict, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
```

**Cập nhật Booking Model:**

```python
# File: backend/restaurant_booking/models/booking.py

class Booking(DateTimeModel, SoftDeleteModel):
    # ... existing fields ...

    # THÊM FIELD MỚI:
    requires_deposit = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('NOT_REQUIRED', 'Không yêu cầu'),
            ('PENDING', 'Chờ thanh toán'),
            ('PAID', 'Đã thanh toán'),
            ('REFUNDED', 'Đã hoàn tiền'),
        ],
        default='NOT_REQUIRED'
    )
```

#### 2.2 Payment Service

**File: `backend/restaurant_booking/services/sepay_service.py` (MỚI)**

```python
import os
import hmac
import hashlib
import requests
from django.utils import timezone
from datetime import timedelta

class SepayService:
    """Service tích hợp SePay payment gateway"""

    BASE_URL = os.getenv('SEPAY_BASE_URL', 'https://api.sepay.vn')
    API_KEY = os.getenv('SEPAY_API_KEY')
    API_SECRET = os.getenv('SEPAY_API_SECRET')

    @classmethod
    def create_payment(cls, booking, amount, return_url, cancel_url):
        """
        Tạo payment link từ SePay

        Returns:
            {
                'payment_url': 'https://sepay.vn/pay/xxx',
                'transaction_id': 'TXN123456',
                'expires_at': datetime
            }
        """
        transaction_id = f"BK{booking.code}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

        payload = {
            'amount': int(amount),
            'order_id': transaction_id,
            'description': f'Đặt cọc booking {booking.code}',
            'return_url': return_url,
            'cancel_url': cancel_url,
            'webhook_url': f"{os.getenv('BACKEND_URL')}/api/restaurant-booking/payments/webhook/sepay/",
        }

        signature = cls._generate_signature(payload)
        headers = {
            'Authorization': f'Bearer {cls.API_KEY}',
            'X-Signature': signature,
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{cls.BASE_URL}/v1/payments/create',
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f'SePay API error: {response.text}')

        data = response.json()

        return {
            'payment_url': data['payment_url'],
            'transaction_id': transaction_id,
            'provider_transaction_id': data.get('sepay_transaction_id'),
            'expires_at': timezone.now() + timedelta(minutes=15),
            'payment_data': data
        }

    @classmethod
    def verify_webhook(cls, request):
        """Xác thực webhook từ SePay"""
        signature = request.headers.get('X-Signature')
        if not signature:
            raise ValueError('Missing signature')

        body = request.body.decode('utf-8')
        expected_signature = hmac.new(
            cls.WEBHOOK_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError('Invalid signature')

        import json
        data = json.loads(body)

        return {
            'transaction_id': data['order_id'],
            'status': data['status'],
            'amount': data['amount'],
            'provider_transaction_id': data.get('transaction_id'),
            'raw_data': data
        }
```

#### 2.3 Payment API Endpoints

**File: `backend/restaurant_booking/views/payment_views.py` (MỚI)**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class InitiatePaymentView(APIView):
    """
    POST /api/restaurant-booking/payments/initiate/

    Body: { "booking_id": 123, "payment_method": "SEPAY" }

    Response: { "payment_url": "...", "transaction_id": "..." }
    """
    def post(self, request):
        booking_id = request.data.get('booking_id')
        payment_method = request.data.get('payment_method')

        # Create payment và return payment_url
        # Implementation details...

        return Response({
            'payment_id': payment.id,
            'transaction_id': payment.transaction_id,
            'payment_url': payment.payment_url,
            'expires_at': payment.expires_at.isoformat()
        })

class SepayWebhookView(APIView):
    """POST /api/restaurant-booking/payments/webhook/sepay/"""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            webhook_data = SepayService.verify_webhook(request)
            payment = Payment.objects.get(transaction_id=webhook_data['transaction_id'])

            if webhook_data['status'] == 'success':
                PaymentService.process_payment_success(payment)
            else:
                PaymentService.process_payment_failure(payment, 'Payment failed')

            return Response({'status': 'ok'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)
```

#### 2.4 Frontend Payment Implementation

**File: `frontend/src/pages/Payment/PaymentSelect.jsx` (MỚI)**

```jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { paymentAPI } from "../../api/payment";

const PaymentSelect = () => {
  const navigate = useNavigate();
  const [selectedMethod, setSelectedMethod] = useState(null);

  const paymentMethods = [
    { id: "SEPAY", name: "SePay", icon: "💳" },
    { id: "CRYPTO_USDT", name: "USDT", icon: "₮" },
    { id: "CRYPTO_BTC", name: "Bitcoin", icon: "₿" },
  ];

  const handlePayment = async () => {
    const response = await paymentAPI.initiatePayment({
      booking_id: booking.id,
      payment_method: selectedMethod,
    });

    if (selectedMethod === "SEPAY") {
      window.location.href = response.payment_url;
    } else {
      navigate("/payment/crypto", { state: { payment: response } });
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Thanh toán đặt cọc</h1>

      {paymentMethods.map((method) => (
        <button
          key={method.id}
          onClick={() => setSelectedMethod(method.id)}
          className={`w-full p-4 border-2 rounded-lg ${
            selectedMethod === method.id ? "border-blue-500" : "border-gray-200"
          }`}
        >
          <span className="text-3xl mr-4">{method.icon}</span>
          {method.name}
        </button>
      ))}

      <button
        onClick={handlePayment}
        className="w-full bg-blue-600 text-white py-3 mt-6"
      >
        Tiếp tục thanh toán
      </button>
    </div>
  );
};
```

**File: `frontend/src/pages/Payment/PaymentCrypto.jsx` (MỚI)**

```jsx
import QRCode from "qrcode.react";

const PaymentCrypto = () => {
  const { payment } = location.state;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Thanh toán Cryptocurrency</h1>

      <div className="text-center mb-6">
        <QRCode value={payment.crypto_address} size={256} />
      </div>

      <div>
        <label>Địa chỉ ví {payment.crypto_network}</label>
        <input
          type="text"
          value={payment.crypto_address}
          readOnly
          className="w-full px-3 py-2 border"
        />
      </div>

      <div className="mt-4">
        <label>Số lượng</label>
        <input
          type="text"
          value={`${payment.crypto_amount} ${payment.crypto_network}`}
          readOnly
          className="w-full px-3 py-2 border"
        />
      </div>
    </div>
  );
};
```

---

### 3. Telegram Notifications via n8n

#### 3.1 Database Schema

**File: `backend/common/models/notification.py` (MỚI)**

```python
from django.db import models
from common.models import DateTimeModel

class Notification(DateTimeModel):
    """Model lưu trữ lịch sử notification"""

    class NotificationType(models.TextChoices):
        BOOKING_CREATED = "BOOKING_CREATED", "Đặt bàn mới"
        PAYMENT_SUCCESS = "PAYMENT_SUCCESS", "Thanh toán thành công"
        BOOKING_CANCELLED = "BOOKING_CANCELLED", "Hủy đặt bàn"
        BOOKING_REMINDER = "BOOKING_REMINDER", "Nhắc nhở"

    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    booking = models.ForeignKey('restaurant_booking.Booking', on_delete=models.CASCADE, null=True)
    payment = models.ForeignKey('restaurant_booking.Payment', on_delete=models.CASCADE, null=True)

    telegram_chat_id = models.CharField(max_length=100, null=True)
    telegram_message_id = models.CharField(max_length=100, null=True)
    n8n_execution_id = models.CharField(max_length=100, null=True)

    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)

    notification_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'notifications'
```

**Cập nhật UserInfo Model:**

```python
# File: backend/accounts/models/user_info.py

class UserInfo(DateTimeModel, SoftDeleteModel):
    # ... existing fields ...

    # THÊM FIELD MỚI:
    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    notification_enabled = models.BooleanField(default=True)
```

#### 3.2 Notification Service

**File: `backend/common/services/notification_service.py` (MỚI)**

```python
import os
import requests
from django.utils import timezone
from common.models.notification import Notification

class NotificationService:
    """Service gửi notification đến n8n"""

    N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
    N8N_API_KEY = os.getenv('N8N_API_KEY')

    @classmethod
    def send_to_n8n(cls, webhook_path, data):
        """Gửi webhook đến n8n"""
        url = f"{cls.N8N_WEBHOOK_URL}/{webhook_path}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {cls.N8N_API_KEY}'
        }

        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    @classmethod
    def notify_booking_created(cls, booking):
        """Gửi notification khi có booking mới"""
        data = {
            'type': 'BOOKING_CREATED',
            'booking': {
                'code': booking.code,
                'guest_name': booking.guest_name,
                'booking_date': str(booking.booking_date),
                'booking_time': str(booking.booking_time),
                'party_size': booking.party_size,
            },
            'admin': {
                'telegram_chat_id': os.getenv('TELEGRAM_ADMIN_CHAT_ID'),
            }
        }

        notification = Notification.objects.create(
            notification_type=Notification.NotificationType.BOOKING_CREATED,
            booking=booking,
            notification_data=data
        )

        try:
            response = cls.send_to_n8n('booking-created', data)
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.response_data = response
            notification.save()
            return True
        except Exception as e:
            notification.error_message = str(e)
            notification.save()
            return False

    @classmethod
    def notify_payment_success(cls, payment):
        """Gửi notification khi thanh toán thành công"""
        booking = payment.booking

        data = {
            'type': 'PAYMENT_SUCCESS',
            'payment': {
                'transaction_id': payment.transaction_id,
                'amount': float(payment.amount),
            },
            'booking': {
                'code': booking.code,
                'guest_name': booking.guest_name,
            },
            'admin': {
                'telegram_chat_id': os.getenv('TELEGRAM_ADMIN_CHAT_ID'),
            }
        }

        notification = Notification.objects.create(
            notification_type=Notification.NotificationType.PAYMENT_SUCCESS,
            booking=booking,
            payment=payment,
            notification_data=data
        )

        try:
            response = cls.send_to_n8n('payment-success', data)
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save()
            return True
        except Exception as e:
            notification.error_message = str(e)
            notification.save()
            return False
```

#### 3.3 n8n Workflows

**Workflow 1: Booking Created Notification**

```
Name: Restaurant Booking - New Booking Alert

Nodes:
1. Webhook Trigger
   - Path: /booking-created
   - Method: POST

2. Send to User (Telegram node)
   - Chat ID: {{$json["user"]["telegram_chat_id"]}}
   - Message:
     🎉 Đặt bàn thành công!
     📋 Mã: {{$json["booking"]["code"]}}
     📅 Ngày: {{$json["booking"]["booking_date"]}}
     🕐 Giờ: {{$json["booking"]["booking_time"]}}

3. Send to Admin Group
   - Chat ID: {{$json["admin"]["telegram_chat_id"]}}
   - Message: 🔔 BOOKING MỚI
     👤 Khách: {{$json["booking"]["guest_name"]}}
     📋 Mã: {{$json["booking"]["code"]}}

4. Response
   - Return execution ID
```

**Workflow 2: Payment Success Notification**

```
Name: Restaurant Booking - Payment Success

Nodes:
1. Webhook Trigger
   - Path: /payment-success

2. Send to User
   - Message:
     ✅ THANH TOÁN THÀNH CÔNG!
     💰 Số tiền: {{$json["payment"]["amount"]}}
     📋 Booking: {{$json["booking"]["code"]}}

3. Send to Admin
   - Payment details notification
```

**Workflow 3: Daily Booking Reminder**

```
Name: Restaurant Booking - Daily Reminders

Nodes:
1. Schedule Trigger
   - Cron: 0 9 * * * (9 AM daily)

2. HTTP Request
   - GET {{$env.BACKEND_URL}}/api/restaurant-booking/bookings/today/

3. Loop Over Bookings

4. Send Reminder
   - Message: ⏰ NHẮC NHỞ ĐẶT BÀN
     Bạn có lịch đặt bàn HÔM NAY
```

---

## 📦 ENVIRONMENT VARIABLES

### Backend `.env` (CẬP NHẬT)

```bash
# Database
POSTGRES_DB=ai_chat_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Django
APPLICATION_SECRET=django-insecure-change-this
DEBUG=True

# CORS & URLs
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8001
WEBSITE_URL=http://localhost:5173
BACKEND_URL=http://localhost:8001

# SePay Payment
SEPAY_BASE_URL=https://api.sepay.vn
SEPAY_API_KEY=your_sepay_api_key
SEPAY_API_SECRET=your_sepay_secret
SEPAY_WEBHOOK_SECRET=your_webhook_secret

# Crypto Payment
CRYPTO_PUBLIC_KEY=your_coinpayments_public_key
CRYPTO_PRIVATE_KEY=your_coinpayments_private_key
CRYPTO_IPN_SECRET=your_ipn_secret

# n8n Webhooks
N8N_WEBHOOK_URL=https://your-n8n.com/webhook
N8N_API_KEY=your_n8n_api_key

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id
```

---

## 📅 TIMELINE & MILESTONES

### **Phase 1: Authentication & User Management (Tuần 1-3)**

**Tuần 1: Backend Auth Enhancement**

- [ ] Update Booking model, create migration
- [ ] Implement user booking views
- [ ] Add permission classes
- [ ] Unit tests

**Tuần 2: Frontend Auth Pages**

- [ ] Create AuthContext và ProtectedRoute
- [ ] Build Login, Register pages
- [ ] Update App.jsx với route guards
- [ ] Integration testing

**Tuần 3: User Dashboard**

- [ ] Build UserLayout với sidebar
- [ ] Build MyBookings page
- [ ] Build UserProfile page
- [ ] Testing

**Deliverables:**

- ✅ Users đăng ký/đăng nhập được
- ✅ Route protection hoạt động
- ✅ User xem được bookings của mình

---

### **Phase 2: Admin Interface (Tuần 4-5)**

**Tuần 4: Backend Admin APIs**

- [ ] Create RestaurantSettings model
- [ ] Implement admin booking views
- [ ] Implement admin table management
- [ ] Admin dashboard stats

**Tuần 5: Frontend Admin Dashboard**

- [ ] Build AdminLayout
- [ ] Build AdminDashboard với charts
- [ ] Build AdminBookings table
- [ ] Build AdminTables CRUD

**Deliverables:**

- ✅ Admin có dashboard riêng
- ✅ Admin quản lý được tất cả bookings
- ✅ Admin CRUD tables

---

### **Phase 3: Payment Integration (Tuần 6-9)**

**Tuần 6: Payment Models & SePay**

- [ ] Create Payment model
- [ ] Implement SepayService
- [ ] PaymentService
- [ ] Testing với sandbox

**Tuần 7: Payment Endpoints**

- [ ] Payment initiation endpoint
- [ ] SePay webhook với signature verification
- [ ] Payment status endpoint
- [ ] Testing

**Tuần 8: Crypto Payment**

- [ ] CryptoPaymentService
- [ ] Crypto webhook
- [ ] Testing

**Tuần 9: Frontend Payment UI**

- [ ] Install qrcode.react
- [ ] Build PaymentSelect page
- [ ] Build PaymentCrypto page
- [ ] Payment status polling
- [ ] End-to-end testing

**Deliverables:**

- ✅ SePay payment hoạt động
- ✅ Crypto payment functional
- ✅ Webhook secure

---

### **Phase 4: Telegram Notifications (Tuần 10-11)**

**Tuần 10: n8n & Telegram Setup**

- [ ] Setup n8n instance
- [ ] Create Telegram bot
- [ ] Build n8n workflows
- [ ] Test workflows

**Tuần 11: Backend Integration**

- [ ] Create Notification model
- [ ] Implement NotificationService
- [ ] Integrate triggers
- [ ] Testing

**Deliverables:**

- ✅ Telegram bot hoạt động
- ✅ n8n workflows tự động
- ✅ Admin nhận alert

---

### **Phase 5: Testing & Deployment (Tuần 12)**

- [ ] End-to-end testing
- [ ] Security audit
- [ ] Performance testing
- [ ] Deploy to production

---

## 🔧 TECHNICAL STACK

### Backend

```
✅ Django 6.0
✅ Django REST Framework
✅ Simple JWT
✅ PostgreSQL
✨ Celery + Redis (optional)
```

### Frontend

```
✅ React 19
✅ TailwindCSS 4
✨ @tanstack/react-query
✨ react-hook-form
✨ qrcode.react
✨ recharts
```

### External Services

```
✨ SePay (payment)
✨ CoinPayments (crypto)
✨ n8n (automation)
✨ Telegram Bot API
```

---

## 🔒 SECURITY CHECKLIST

- [x] JWT với expiry ✅
- [ ] Rate limiting
- [ ] Webhook signature verification (CRITICAL!)
- [ ] HTTPS in production
- [ ] Transaction idempotency
- [ ] Payment timeout
- [x] CORS configured ✅
- [x] CSRF protection ✅

---

## 📈 SUCCESS METRICS

- User registration rate > 40%
- Booking completion rate > 80%
- Payment success rate > 95%
- API response time < 200ms
- Uptime > 99.5%

---

## 🚨 RISKS & MITIGATION

### Risk 1: Payment Gateway Downtime

**Mitigation:** Fallback to manual payment, retry queue

### Risk 2: n8n Webhook Failures

**Mitigation:** Retry logic (3 attempts), email fallback

### Risk 3: Token Refresh Race Conditions

**Mitigation:** ✅ Already handled in axios interceptor

---

## 💬 Q&A

### Q: Guest có thể đặt bàn không cần đăng nhập không?

**A:** CÓ! Guest booking vẫn được giữ nguyên.

### Q: Admin có thể xem booking của guest không?

**A:** CÓ! Admin xem được TẤT CẢ bookings.

### Q: Nếu SePay webhook fail thì sao?

**A:** Có retry mechanism và payment status polling từ frontend.

### Q: User có thể hủy booking đã thanh toán không?

**A:** CÓ nhưng có điều kiện (> 24 giờ trước booking, refund 80%).

---

## 🎯 NEXT STEPS

### Immediate Actions

1. **Review và approve plan này**
2. **Setup development environment**
3. **Start Phase 1 (Week 1)**

### Before Starting

- [ ] Tạo SePay developer account
- [ ] Tạo CoinPayments account
- [ ] Setup n8n instance
- [ ] Create Telegram bot

---

**Kết luận:**

Kế hoạch chi tiết, khả thi trong **9-12 tuần**. Mỗi phase có deliverables rõ ràng.

Architecture được thiết kế để:

- ✅ Tận dụng tối đa infrastructure hiện có
- ✅ Mở rộng dễ dàng cho tương lai
- ✅ Security-first approach
- ✅ User experience tốt

**Sẵn sàng bắt đầu!** 🚀

---

**Tác giả:** GitHub Copilot (Claude Sonnet 4.5)  
**Ngày tạo:** 28/02/2026  
**File:** `IMPLEMENTATION_PLAN.md`
