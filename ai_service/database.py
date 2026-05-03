from datetime import datetime, timezone
from pymongo import MongoClient
from .config import MONGODB_URI, MONGODB_DB

_client = MongoClient(MONGODB_URI)
_db     = _client[MONGODB_DB]

chat_history = _db["chat_history"]


def save_message(user_id: str, session_id: str, role: str, content: str) -> str:
    doc = {
        "user_id":    user_id,
        "session_id": session_id,
        "role":       role,
        "content":    content,
        "created_at": datetime.now(timezone.utc),
    }
    result = chat_history.insert_one(doc)
    return str(result.inserted_id)


def get_history(session_id: str) -> list[dict]:
    docs = chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "user_id": 1, "role": 1, "content": 1, "created_at": 1},
    ).sort("created_at", 1)
    return list(docs)


def get_history_by_user(user_id: str) -> list[dict]:
    docs = chat_history.find(
        {"user_id": user_id},
        {"_id": 0, "session_id": 1, "role": 1, "content": 1, "created_at": 1},
    ).sort("created_at", 1)
    return list(docs)


def delete_history(session_id: str) -> int:
    result = chat_history.delete_many({"session_id": session_id})
    return result.deleted_count
