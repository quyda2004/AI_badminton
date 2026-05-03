# AI Badminton Court Booking — Build Guide

> Đọc file này trước khi build bất cứ thứ gì. Đây là source of truth cho kiến trúc và convention.

---

## Tổng quan kiến trúc (Microservices)

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (SPA)                         │
│              frontend/  ─  port 5500 (Live Server)       │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / REST
                      ▼
         ┌────────────────────────┐
         │     API Gateway        │
         │   nginx  ─  port 80    │
         │                        │
         │  /api/*  → :8000       │
         │  /ai/*   → :8001       │
         └──────┬─────────┬───────┘
                │         │
                ▼         ▼
  ┌─────────────────┐   ┌──────────────────────┐
  │ backend-service │   │     ai-service        │
  │   port 8000     │◄──│   port 8001           │
  │                 │HTTP│                      │
  │ auth            │   │ /ai/chat              │
  │ courts          │   │ /ai/history           │
  │ bookings        │   │ Gemini function call  │
  │ payments        │   │ MCP server            │
  │ admin           │   └──────────┬───────────┘
  └────────┬────────┘             │
           │                      │
           ▼                      ▼
   ┌──────────────┐      ┌──────────────────┐
   │  PostgreSQL  │      │    MongoDB        │
   │  port 5432   │      │   port 27017      │
   │  (app data)  │      │  (chat history)   │
   └──────────────┘      └──────────────────┘
```

---

## Services

### 1. `backend-service` — port 8000

**Thư mục**: `backend/`

**Trách nhiệm**: toàn bộ REST API nghiệp vụ — auth, courts, bookings, payments, admin.

**Chạy**: `uvicorn backend.api.main:app --reload --port 8000`

**Database**: PostgreSQL (users, courts, bookings, payments)

**Endpoints**:
| Router | Prefix | Mô tả |
|--------|--------|-------|
| auth | `/auth` | register, login, /me |
| courts | `/courts` | list, create, availability |
| bookings | `/bookings` | CRUD, cancel, reschedule |
| payments | `/payments` | list payments for booking |
| admin | `/admin` | stats, all bookings |

**Quan trọng**: service này KHÔNG biết AI tồn tại. Nó chỉ expose REST API thuần.

---

### 2. `ai-service` — port 8001

**Thư mục**: `ai_service/`

**Trách nhiệm**: chat AI với Gemini, function calling, MCP server.

**Chạy**: `uvicorn ai_service.main:app --reload --port 8001`

**Database**: MongoDB (chỉ lưu chat history)

**Endpoints**:
| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/ai/chat` | gửi tin nhắn, nhận reply từ Gemini |
| GET | `/ai/history/{session_id}` | lấy lịch sử session |
| GET | `/ai/history` | lấy lịch sử theo user |

---

### Gemini Function Calling — flow chi tiết

Gemini **không tự gọi HTTP** — nó chỉ trả về JSON nói "tao muốn gọi tool X với params Y". Code của mình mới là người thực thi.

```
User: "Đặt sân 1 ngày mai lúc 8h"
        │
        ▼
POST /ai/chat  (ai-service nhận request, có JWT của user)
        │
        ▼
gemini_client.py gửi message + tool definitions lên Gemini API
        │
        ▼
Gemini trả về:  { "tool_call": "create_booking", "params": { ... } }
        │        ← Gemini DỪNG Ở ĐÂY, không tự làm gì thêm
        ▼
ai_service/tools.py nhận lệnh, thực thi tool:
    → gọi HTTP: POST http://backend:8000/bookings
    → đính JWT của user vào header Authorization
        │
        ▼
backend-service xử lý, trả JSON kết quả
        │
        ▼
ai_service/tools.py trả kết quả về cho Gemini (như là "tool result")
        │
        ▼
Gemini đọc kết quả, sinh câu trả lời tiếng Việt cho user
        │
        ▼
Lưu toàn bộ conversation vào MongoDB
        │
        ▼
Trả response về frontend
```

**Điểm mấu chốt**:
- Gemini = bộ não quyết định tool nào cần gọi, params là gì
- `ai_service/tools.py` = người thực thi, gọi HTTP tới backend thay vì query DB trực tiếp
- JWT token của user phải được **truyền xuyên suốt**: từ request `/ai/chat` → giữ trong memory → đính vào mọi HTTP call tới backend
- Backend không biết request đến từ AI hay từ frontend — nó chỉ thấy JWT hợp lệ

**Tool map (tool name → backend endpoint)**:
| Tool | Method | Endpoint backend |
|------|--------|-----------------|
| `get_courts` | GET | `/courts` |
| `check_availability` | GET | `/courts/{id}/availability` |
| `create_booking` | POST | `/bookings` |
| `get_my_bookings` | GET | `/bookings` |
| `cancel_booking` | PUT | `/bookings/{id}/cancel` |
| `cancel_booking_by_info` | GET + PUT | `/bookings` → filter → `/bookings/{id}/cancel` |

**MCP Server**: wrap các tool trên thành MCP protocol để Claude Desktop hoặc agent khác có thể dùng. Chạy cùng process với ai-service.

---

## Cấu trúc thư mục mục tiêu

```
AI_badminton/
├── backend/                    # backend-service
│   ├── api/
│   │   ├── main.py             # FastAPI app, register routers
│   │   ├── auth.py
│   │   ├── courts.py
│   │   ├── bookings.py
│   │   ├── payments.py
│   │   ├── admin.py
│   │   └── deps.py
│   ├── models/                 # SQLAlchemy models (PostgreSQL)
│   ├── schemas/                # Pydantic schemas
│   ├── scripts/                # seed, reset DB
│   ├── config.py
│   ├── db_connect.py
│   └── security.py
│
├── ai_service/                 # ai-service  ← tạo mới, thay thế AI_worker/
│   ├── main.py                 # FastAPI app entry point  (tạo mới)
│   ├── router.py               # /ai/* endpoints          (chuyển từ backend/api/ai.py)
│   ├── gemini_client.py        # Gemini + function calling (chuyển từ AI_worker/)
│   ├── database.py             # MongoDB chat history     (chuyển từ AI_worker/)
│   ├── tools.py                # tool definitions + HTTP calls tới backend (viết lại từ backend/tools/)
│   ├── mcp_server.py           # MCP server               (chuyển từ backend/tools/mcp_server.py)
│   └── config.py               # env vars riêng cho ai-service (tạo mới)
│
├── frontend/                   # SPA tĩnh
│   ├── index.html
│   ├── app.js                  # gọi /api/* và /ai/* qua gateway
│   └── style.css
│
├── nginx/                      # API Gateway  ← tạo mới
│   └── nginx.conf
│
├── tests/                      # integration tests
├── docker-compose.yml          # orchestrate tất cả services
├── .env.example
└── CLAUDE.md                   # file này
```

---

## Docker Compose (môi trường dev)

Khi build docker-compose, mỗi service là 1 container:

| Service | Image | Port |
|---------|-------|------|
| `postgres` | postgres:16 | 5432 |
| `mongodb` | mongo:7 | 27017 |
| `backend` | ./backend | 8000 |
| `ai` | ./ai_service | 8001 |
| `nginx` | ./nginx | 80 |

**Rule**: backend và ai không expose port ra ngoài — tất cả traffic đi qua nginx port 80.

---

## Env Variables

### backend-service (`.env`)
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
POSTGRES_DB=badminton_db
SECRET_KEY=...
```

### ai-service (`.env.ai` hoặc cùng `.env`)
```
GEMINIUS_API_KEY=...
GEMINIUS_MODEL=gemini-2.5-flash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ai_worker_db
BACKEND_SERVICE_URL=http://localhost:8000   # internal URL gọi backend
```

---

## Communication giữa services

### Frontend → Backend
- Frontend gọi `/api/courts`, `/api/bookings`, `/api/auth`...
- nginx nhận, **strip prefix `/api`**, forward tới `backend:8000/courts`, `backend:8000/bookings`...
- Header: `Authorization: Bearer <jwt>`

### Frontend → AI
- Frontend gọi `/ai/chat`, `/ai/history/...`
- nginx nhận, **giữ nguyên path**, forward tới `ai:8001/ai/chat`, `ai:8001/ai/history/...`
- Header: `Authorization: Bearer <jwt>`

> Lý do: backend endpoint gốc là `/courts`, `/bookings`... không có prefix. AI endpoint gốc là `/ai/chat` đã có `/ai/` rồi nên không strip.

### AI Service → Backend Service (internal)
- `ai-service` dùng `httpx` gọi HTTP tới backend, base URL = `BACKEND_SERVICE_URL`
- **Bắt buộc** truyền JWT token của user vào header `Authorization: Bearer <token>` khi gọi
- Token lấy từ request gốc `/ai/chat` của user, giữ trong memory suốt vòng lặp function calling
- Không import code của backend — chỉ giao tiếp qua HTTP

```python
# Ví dụ tool create_booking trong ai_service/tools.py
async def create_booking(court_id, start_time, end_time, user_token: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{BACKEND_SERVICE_URL}/bookings",
            json={"court_id": court_id, "start_time": start_time, "end_time": end_time},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        return res.json()
```

### JWT Verification
- ai-service tự decode JWT bằng cùng `SECRET_KEY` (không gọi thêm network)
- Chỉ cần verify chữ ký và lấy `user_id` từ payload
- `SECRET_KEY` phải giống hệt nhau trong `.env` của cả 2 service

---

## Convention & Rules

### Thêm endpoint mới
1. Thuộc nghiệp vụ (courts, bookings, users...)? → thêm vào `backend-service`
2. Thuộc AI/chat? → thêm vào `ai-service`
3. Không thêm business logic vào ai-service — nó chỉ orchestrate AI

### AI Tools
- Tools trong `ai_service/tools.py` chỉ được gọi HTTP tới backend, KHÔNG query DB trực tiếp
- Mỗi tool map 1-1 với 1 endpoint của backend

### Database ownership
- PostgreSQL: chỉ `backend-service` được đọc/ghi
- MongoDB: chỉ `ai-service` được đọc/ghi
- Không service nào được dùng chung DB connection của service khác

### Code sharing
- Nếu cần share Pydantic schema → tạo `shared/schemas/` hoặc copy thủ công
- Không import chéo giữa `backend/` và `ai_service/`

---

## Thứ tự build

```
1. backend-service    → chạy được độc lập, test bằng curl/Postman
2. ai-service         → sau khi backend chạy xong, vì ai gọi backend
3. nginx config       → sau khi cả 2 service chạy được
4. docker-compose     → đóng gói hết lại
5. frontend update    → đổi base URL về gateway port 80
```

---

## Chạy dev (không Docker)

```bash
# Terminal 1 — backend
cd D:/AI_caulong/AI_badminton
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — ai-service
uvicorn ai_service.main:app --reload --port 8001

# Terminal 3 — frontend
# Dùng VS Code Live Server hoặc:
python -m http.server 5500 --directory frontend
```

---

## Checklist trước khi build 1 service mới

- [ ] Xác định service thuộc nhóm nào (backend / ai / gateway)
- [ ] Đọc phần service tương ứng trong CLAUDE.md
- [ ] Không gọi DB của service khác
- [ ] Communication qua HTTP, không import chéo
- [ ] Env vars đã có trong `.env.example`
- [ ] Viết test trước khi kết nối với service khác
