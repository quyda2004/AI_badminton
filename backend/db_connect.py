import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, inspect

from .models import Base  # __init__.py tự import User, Court, Booking, Payment → Base.metadata biết hết
from .config import DATABASE_URL, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB


def create_db_if_not_exists():
    conn = psycopg2.connect(host=POSTGRES_HOST, port=POSTGRES_PORT, user=POSTGRES_USER, password=POSTGRES_PASSWORD, dbname="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES_DB,))
    exists = cur.fetchone()

    if exists:
        print(f"[OK] Database '{POSTGRES_DB}' đã tồn tại → kết nối vào")
    else:
        cur.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
        print(f"[OK] Database '{POSTGRES_DB}' chưa có → đã tạo mới")

    cur.close()
    conn.close()


def create_tables(engine):
    Base.metadata.create_all(engine)
    print("[OK] Tạo tables xong")


def check_tables(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[INFO] Tables hiện có: {tables}")


if __name__ == "__main__":
    create_db_if_not_exists()

    engine = create_engine(DATABASE_URL, echo=False)
    create_tables(engine)
    check_tables(engine)

    engine.dispose()
    print("[DONE] Hoàn tất!")
