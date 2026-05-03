import uuid
import json

from google import genai
from google.genai import types

from .config import GEMINIUS_API_KEY, GEMINIUS_MODEL
from .database import save_message, get_history
from . import tools

client = genai.Client(api_key=GEMINIUS_API_KEY)

SYSTEM_PROMPT = (
    "Bạn là trợ lý đặt sân cầu lông. Trả lời ngắn gọn, tối đa 25 từ. "
    "Không bao giờ hỏi booking_id hay court_id — đó là thông tin nội bộ, user không biết.\n\n"
    "Quy trình ĐẶT SÂN:\n"
    "1. Gọi get_courts() để lấy danh sách sân và ID thật.\n"
    "2. Tìm sân khớp với mô tả của user (theo tên hoặc số thứ tự).\n"
    "3. Gọi check_availability() để kiểm tra slot trống và giá.\n"
    "4. Thông báo giá cho user, rồi gọi create_booking() để đặt.\n\n"
    "Quy trình HỦY SÂN:\n"
    "1. Gọi get_my_bookings() để lấy danh sách booking của user.\n"
    "2. Tìm booking khớp với mô tả của user (theo tên sân, ngày, giờ).\n"
    "3. Gọi cancel_booking() với booking_id tìm được — không hỏi user.\n\n"
    "Không bao giờ tự đoán ID — phải lấy từ tools."
)

TOOL_DECLARATIONS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_courts",
        description="Lấy danh sách tất cả sân cầu lông đang hoạt động.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="check_availability",
        description="Kiểm tra slot giờ trống của 1 sân theo ngày.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "court_id": types.Schema(type=types.Type.STRING, description="ID của sân"),
                "date_str": types.Schema(type=types.Type.STRING, description="Ngày cần kiểm tra, định dạng YYYY-MM-DD"),
            },
            required=["court_id", "date_str"],
        ),
    ),
    types.FunctionDeclaration(
        name="create_booking",
        description="Đặt sân cầu lông cho user.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "court_id":   types.Schema(type=types.Type.STRING,  description="ID sân"),
                "date_str":   types.Schema(type=types.Type.STRING,  description="Ngày đặt, định dạng YYYY-MM-DD"),
                "start_hour": types.Schema(type=types.Type.INTEGER, description="Giờ bắt đầu (6-21)"),
                "end_hour":   types.Schema(type=types.Type.INTEGER, description="Giờ kết thúc (7-22)"),
            },
            required=["court_id", "date_str", "start_hour", "end_hour"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_my_bookings",
        description="Lấy danh sách booking của user hiện tại.",
        parameters=types.Schema(type=types.Type.OBJECT, properties={}),
    ),
    types.FunctionDeclaration(
        name="cancel_booking",
        description="Hủy một booking theo booking_id.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "booking_id": types.Schema(type=types.Type.STRING, description="ID booking cần hủy"),
            },
            required=["booking_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="cancel_booking_by_info",
        description="Hủy booking theo tên sân, ngày và giờ bắt đầu — không cần booking_id.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "court_name": types.Schema(type=types.Type.STRING,  description="Tên sân hoặc một phần tên sân, vd: 'sân 2'"),
                "date_str":   types.Schema(type=types.Type.STRING,  description="Ngày, định dạng YYYY-MM-DD"),
                "start_hour": types.Schema(type=types.Type.INTEGER, description="Giờ bắt đầu (6-21)"),
            },
            required=["court_name", "date_str", "start_hour"],
        ),
    ),
])


def _run_tool(name: str, args: dict, token: str) -> str:
    """Thực thi tool bằng cách gọi HTTP tới backend-service."""
    if name == "get_courts":
        result = tools.get_courts(token)
    elif name == "check_availability":
        result = tools.check_availability(token=token, **args)
    elif name == "create_booking":
        result = tools.create_booking(token=token, **args)
    elif name == "get_my_bookings":
        result = tools.get_my_bookings(token)
    elif name == "cancel_booking":
        result = tools.cancel_booking(token=token, **args)
    elif name == "cancel_booking_by_info":
        result = tools.cancel_booking_by_info(token=token, **args)
    else:
        result = {"error": f"Tool '{name}' không tồn tại"}
    return json.dumps(result, ensure_ascii=False)


def chat_with_user(user_id: str, token: str, prompt: str, session_id: str | None = None) -> dict:
    """
    Gọi Gemini với function calling, lưu lịch sử vào MongoDB.
    token: JWT của user, dùng để gọi HTTP tới backend.
    Trả về { session_id, reply }
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    history  = get_history(session_id)
    contents = [{"role": msg["role"], "parts": [{"text": msg["content"]}]} for msg in history]
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[TOOL_DECLARATIONS],
    )

    while True:
        response = client.models.generate_content(
            model=GEMINIUS_MODEL,
            contents=contents,
            config=config,
        )

        part = response.candidates[0].content.parts[0]

        if part.function_call:
            fn          = part.function_call
            tool_result = _run_tool(fn.name, dict(fn.args), token)

            contents.append({"role": "model", "parts": [{"function_call": {"name": fn.name, "args": dict(fn.args)}}]})
            contents.append({"role": "user",  "parts": [{"function_response": {"name": fn.name, "response": {"result": tool_result}}}]})
        else:
            reply = part.text
            break

    save_message(user_id=user_id, session_id=session_id, role="user",  content=prompt)
    save_message(user_id=user_id, session_id=session_id, role="model", content=reply)

    return {"session_id": session_id, "reply": reply}
