# Models Map — AI Badminton

## Tổng quan

Folder `models/` = các bảng thật trong **PostgreSQL**.
Mỗi class = 1 table. Dùng **SQLAlchemy 2.0 async** với `Mapped` + `mapped_column`.

---

## Quan hệ giữa các bảng

```
users
  │
  │ 1 user đặt nhiều booking
  │ (1 ──< N)
  ▼
bookings ────────────► courts
  │         N booking       1 sân được đặt nhiều lần
  │         dùng 1 sân      (N ──< 1)
  │
  │ 1 booking có nhiều payment
  │ (1 ──< N)
  ▼
payments
```

---

## 1. User — `users`

**File:** `apps/backend/app/models/user.py`

| Column | Type | Ghi chú |
|--------|------|---------|
| `id` | String(36) PK | UUID tự sinh |
| `email` | String(255) | unique, index, bắt buộc |
| `phone` | String(20) | optional |
| `full_name` | String(255) | bắt buộc |
| `hashed_password` | String(255) | bắt buộc, đã hash bcrypt |
| `role` | String(20) | default = `"user"` / `"admin"` |
| `created_at` | DateTime(tz) | tự set khi INSERT |
| `updated_at` | DateTime(tz) | tự update khi UPDATE |

---

## 2. Court — `courts`

**File:** `apps/backend/app/models/court.py`

| Column | Type | Ghi chú |
|--------|------|---------|
| `id` | String(36) PK | UUID tự sinh |
| `name` | String(100) | bắt buộc |
| `type` | String(50) | default = `"standard"` |
| `price_per_hour` | Numeric(10,2) | bắt buộc |
| `status` | String(20) | default = `"active"` / `"inactive"` |
| `description` | Text | optional |

---

## 3. Booking — `bookings`

**File:** `apps/backend/app/models/booking.py`

| Column | Type | Ghi chú |
|--------|------|---------|
| `id` | String(36) PK | UUID tự sinh |
| `user_id` | String(36) FK | → `users.id` |
| `court_id` | String(36) FK | → `courts.id` |
| `start_time` | DateTime(tz) | bắt buộc |
| `end_time` | DateTime(tz) | bắt buộc |
| `status` | String(20) | default = `"confirmed"` / `"cancelled"` |
| `total_price` | Numeric(10,2) | server tự tính = giá sân × số giờ |
| `created_at` | DateTime(tz) | tự set khi INSERT |
| `updated_at` | DateTime(tz) | tự update khi UPDATE |

---

## 4. Payment — `payments`

**File:** `apps/backend/app/models/payment.py`

| Column | Type | Ghi chú |
|--------|------|---------|
| `id` | String(36) PK | UUID tự sinh |
| `booking_id` | String(36) FK | → `bookings.id` |
| `amount` | Numeric(10,2) | bắt buộc |
| `method` | String(50) | default = `"cash"` |
| `status` | String(20) | default = `"pending"` / `"paid"` |
| `paid_at` | DateTime(tz) | optional, set khi thanh toán xong |
| `created_at` | DateTime(tz) | tự set khi INSERT |

---

## Lưu ý quan trọng

- Tất cả `id` dùng **UUID** (String 36 ký tự) thay vì auto-increment integer
- Tất cả `DateTime` có `timezone=True` → lưu dạng UTC
- `models/` chỉ định nghĩa cấu trúc bảng — **không chứa logic**
- Logic nghiệp vụ nằm ở `services/`, không viết vào đây