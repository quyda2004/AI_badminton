import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from config import DATABASE_URL, SECRET_KEY, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_DB
from models import User, Court, Booking, Payment
from security import verify_password

engine = create_engine(DATABASE_URL, echo=False)

SEP = "-" * 50


def check_config():
    print(f"\n{'-'*50}")
    print("  CONFIG")
    print(SEP)
    print(f"  Host       : {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"  User       : {POSTGRES_USER}")
    print(f"  Database   : {POSTGRES_DB}")
    print(f"  Secret Key : {SECRET_KEY[:20]}...")


def check_db_connection():
    print(f"\n{SEP}")
    print("  KẾT NỐI DATABASE")
    print(SEP)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  [OK] Kết nối PostgreSQL thành công")
    except Exception as e:
        print(f"  [FAIL] Không kết nối được: {e}")


def check_tables():
    print(f"\n{SEP}")
    print("  TABLES")
    print(SEP)
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
    expected = {"users", "courts", "bookings", "payments"}
    for t in expected:
        status = "[OK]" if t in tables else "[MISS]"
        print(f"  {status} {t}")


def check_data():
    print(f"\n{SEP}")
    print("  DATA TRONG DB")
    print(SEP)
    with Session(engine) as db:
        users    = db.query(User).count()
        courts   = db.query(Court).count()
        bookings = db.query(Booking).count()
        payments = db.query(Payment).count()
    print(f"  users    : {users}")
    print(f"  courts   : {courts}")
    print(f"  bookings : {bookings}")
    print(f"  payments : {payments}")


def check_passwords():
    print(f"\n{SEP}")
    print("  KIỂM TRA PASSWORD (bcrypt hash thật)")
    print(SEP)
    test_cases = [
        ("nguyen.vana@gmail.com", "123"),
        ("admin@badminton.com",   "admin"),
    ]
    with Session(engine) as db:
        for email, password in test_cases:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"  [MISS] {email} — không tìm thấy trong DB")
                continue
            try:
                ok = verify_password(password, user.hashed_password)
                status = "[OK]" if ok else "[FAIL] password không khớp"
            except Exception as e:
                status = f"[FAIL] hash lỗi ({e}) → cần chạy lại reset_db.py"
            print(f"  {status} {email}")


def check_secret_key():
    print(f"\n{SEP}")
    print("  SECRET KEY")
    print(SEP)
    if SECRET_KEY == "change-this":
        print("  [WARN] Đang dùng default key — .env chưa được đọc!")
        print("         Chạy uvicorn từ thư mục E:\\AI_badminton")
    else:
        print("  [OK] SECRET_KEY đã được load từ .env")


if __name__ == "__main__":
    print("\n  BADMINTON — DIAGNOSTIC CHECK")
    check_config()
    check_db_connection()
    check_tables()
    check_data()
    check_passwords()
    check_secret_key()
    print(f"\n{SEP}\n")
