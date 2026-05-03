from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .deps import get_current_user
from ..models import User
from AI_worker.gemini_client import chat_with_user
from AI_worker.database import get_history, get_history_by_user

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/chat", response_model=ChatResponse)
def ai_chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    result = chat_with_user(
        user_id=current_user.id,
        prompt=req.message,
        session_id=req.session_id,
    )
    return ChatResponse(session_id=result["session_id"], reply=result["reply"])


@router.get("/history/{session_id}")
def session_history(session_id: str, current_user: User = Depends(get_current_user)):
    return get_history(session_id)


@router.get("/history")
def user_history(current_user: User = Depends(get_current_user)):
    return get_history_by_user(current_user.id)
