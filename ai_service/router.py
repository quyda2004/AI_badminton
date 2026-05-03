from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from .config import SECRET_KEY
from .gemini_client import chat_with_user
from .database import get_history, get_history_by_user

router = APIRouter(prefix="/ai", tags=["ai"])
_bearer = HTTPBearer()

ALGORITHM = "HS256"


class ChatRequest(BaseModel):
    message:    str
    session_id: str | None = None


class ChatResponse(BaseModel):
    user_id:    str
    session_id: str
    reply:      str


def _get_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """Decode JWT cục bộ — không cần gọi backend."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")
    return {"user_id": user_id, "token": token}


@router.post("/chat", response_model=ChatResponse)
def ai_chat(req: ChatRequest, user: dict = Depends(_get_user)):
    result = chat_with_user(
        user_id=user["user_id"],
        token=user["token"],
        prompt=req.message,
        session_id=req.session_id,
    )
    return ChatResponse(user_id=user["user_id"], session_id=result["session_id"], reply=result["reply"])


@router.get("/history/{session_id}")
def session_history(session_id: str, user: dict = Depends(_get_user)):
    return get_history(session_id)


@router.get("/history")
def user_history(user: dict = Depends(_get_user)):
    return get_history_by_user(user["user_id"])
