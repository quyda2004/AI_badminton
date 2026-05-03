import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
_db = _client[os.getenv("MONGODB_DB", "ai_worker_db")]

chat_history = _db["chat_history"]


def save_message(user_id: str, session_id: str, role: str, content: str) -> str:
    """Lưu 1 tin nhắn vào lịch sử. role: 'user' hoặc 'model'"""
    doc = {
        "user_id": user_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow(),
    }
    result = chat_history.insert_one(doc)
    return str(result.inserted_id)


def get_history(session_id: str) -> list[dict]:
    """Lấy toàn bộ lịch sử chat theo session_id, sắp xếp theo thời gian."""
    docs = chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "user_id": 1, "role": 1, "content": 1, "created_at": 1},
    ).sort("created_at", 1)
    return list(docs)


def get_history_by_user(user_id: str) -> list[dict]:
    """Lấy toàn bộ lịch sử chat của 1 user, sắp xếp theo thời gian."""
    docs = chat_history.find(
        {"user_id": user_id},
        {"_id": 0, "session_id": 1, "role": 1, "content": 1, "created_at": 1},
    ).sort("created_at", 1)
    return list(docs)


def delete_history(session_id: str) -> int:
    """Xóa toàn bộ lịch sử của 1 session. Trả về số document đã xóa."""
    result = chat_history.delete_many({"session_id": session_id})
    return result.deleted_count
