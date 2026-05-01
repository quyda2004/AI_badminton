from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.auth     import router as auth_router
from api.courts   import router as courts_router
from api.bookings import router as bookings_router
from api.payments import router as payments_router

app = FastAPI(title="Badminton API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(courts_router)
app.include_router(bookings_router)
app.include_router(payments_router)


@app.get("/health")
def health():
    return {"status": "ok"}
