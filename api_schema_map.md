# API & Schema Map — AI Badminton

## Tổng quan

Mỗi API endpoint dùng **schema** theo 2 chiều:
- **INPUT** (`req: SchemaName`) — validate JSON client gửi lên
- **OUTPUT** (`response_model=SchemaName`) — filter data server trả về

---

## 1. Auth — `/api/auth`

| Method | Endpoint | INPUT Schema | OUTPUT Schema | Ghi chú |
|--------|----------|-------------|--------------|---------|
| POST | `/api/auth/register` | `RegisterRequest` | `UserResponse` | Tạo tài khoản mới |
| POST | `/api/auth/login` | `LoginRequest` | `TokenResponse` | Trả về JWT token |
| GET | `/api/auth/me` | _(không có body)_ | `UserResponse` | Lấy thông tin user hiện tại |

### Schemas dùng (`schemas/auth.py`)

```
RegisterRequest   → email, password, full_name, phone(optional)
LoginRequest      → email, password
TokenResponse     → access_token, token_type
UserResponse      → id, email, full_name, phone, role
```

---

## 2. Courts — `/api/courts`

| Method | Endpoint | INPUT Schema | OUTPUT Schema | Ghi chú |
|--------|----------|-------------|--------------|---------|
| GET | `/api/courts` | _(không có body)_ | `list[CourtResponse]` | Lấy danh sách sân |
| POST | `/api/courts` | `CourtCreate` | `CourtResponse` | Tạo sân mới (admin only) |
| GET | `/api/courts/{court_id}/availability` | `date` (query param) | `list[TimeSlot]` | Xem slot trống theo ngày |

### Schemas dùng (`schemas/court.py`)

```
CourtCreate     → name, type, price_per_hour, status, description
CourtResponse   → id, name, type, price_per_hour, status, description
TimeSlot        → start, end, available
```

---

## 3. Bookings — `/api/bookings`

| Method | Endpoint | INPUT Schema | OUTPUT Schema | Ghi chú |
|--------|----------|-------------|--------------|---------|
| GET | `/api/bookings` | _(không có body)_ | `list[BookingResponse]` | Lấy danh sách booking của user |
| POST | `/api/bookings` | `BookingCreate` | `BookingResponse` | Tạo booking mới |
| GET | `/api/bookings/{booking_id}` | _(không có body)_ | `BookingResponse` | Lấy chi tiết 1 booking |
| PUT | `/api/bookings/{booking_id}/cancel` | _(không có body)_ | `BookingResponse` | Huỷ booking |
| PUT | `/api/bookings/{booking_id}/reschedule` | `RescheduleRequest` | `BookingResponse` | Đổi lịch booking |

### Schemas dùng (`schemas/booking.py`)

```
BookingCreate      → court_id, start_time, end_time
RescheduleRequest  → new_start_time, new_end_time
BookingResponse    → id, user_id, court_id, start_time, end_time, status, total_price, created_at
```

---

## 4. Admin — `/api/admin`

| Method | Endpoint | INPUT Schema | OUTPUT Schema | Ghi chú |
|--------|----------|-------------|--------------|---------|
| GET | `/api/admin/stats` | _(không có body)_ | `DashboardStats` | Thống kê tổng quan (admin only) |
| GET | `/api/admin/bookings` | `status` (query param, optional) | _(raw list)_ | Lấy tất cả booking, lọc theo status |
| GET | `/api/admin/users` | _(không có body)_ | _(raw list)_ | Lấy tất cả user |

### Schemas dùng (`schemas/admin.py`)

```
DashboardStats  → total_bookings, total_revenue, active_courts, total_users, bookings_today
```

---

## 5. Chat — `/api/chat`

| Method | Endpoint | INPUT Schema | OUTPUT Schema | Ghi chú |
|--------|----------|-------------|--------------|---------|
| POST | `/api/chat` | `ChatRequest` | `ChatTaskResponse` | Gửi tin nhắn → đẩy vào Redis queue |
| GET | `/api/chat/status/{task_id}` | _(không có body)_ | `ChatStatusResponse` | Poll kết quả AI từ Redis |
| GET | `/api/chat/history` | _(không có body)_ | `list[MessageItem]` | Lấy lịch sử chat từ MongoDB |

### Schemas dùng (`schemas/chat.py`)

```
ChatRequest         → message
ChatTaskResponse    → task_id
ChatStatusResponse  → status, text(optional)
MessageItem         → role, content, timestamp
```

---

## Sơ đồ tổng quan

```
schemas/auth.py      ←→   api/auth.py
schemas/court.py     ←→   api/courts.py
schemas/booking.py   ←→   api/bookings.py
schemas/admin.py     ←→   api/admin.py
schemas/chat.py      ←→   api/chat.py
```

## Lưu ý về DB backend mỗi API dùng

| API | Database |
|-----|----------|
| auth, courts, bookings, admin | PostgreSQL (qua SQLAlchemy) |
| chat (gửi + poll status) | Redis (queue + cache kết quả) |
| chat (lịch sử) | MongoDB (lưu session chat) |
