"""
MCP server — wrap các tool của ai_service để Claude Desktop hoặc agent khác dùng.
Chạy độc lập: python -m ai_service.mcp_server
"""
from mcp.server.fastmcp import FastMCP
from . import tools

mcp = FastMCP("Badminton Tools")

# MCP tools không có JWT context nên dùng token rỗng.
# Khi tích hợp thật, truyền token qua biến môi trường hoặc config riêng.
_TOKEN = ""


@mcp.tool()
def tool_get_courts() -> list[dict]:
    """Lấy danh sách tất cả sân cầu lông đang hoạt động."""
    return tools.get_courts(_TOKEN)


@mcp.tool()
def tool_check_availability(court_id: str, date_str: str) -> list[dict]:
    """
    Kiểm tra slot giờ trống của 1 sân theo ngày.
    - court_id: ID của sân
    - date_str: ngày cần kiểm tra, định dạng YYYY-MM-DD
    """
    return tools.check_availability(token=_TOKEN, court_id=court_id, date_str=date_str)


@mcp.tool()
def tool_create_booking(token: str, court_id: str, date_str: str, start_hour: int, end_hour: int) -> dict:
    """
    Đặt sân cho user.
    - token: JWT của user
    - court_id: ID sân
    - date_str: ngày đặt, định dạng YYYY-MM-DD
    - start_hour: giờ bắt đầu (6-21)
    - end_hour: giờ kết thúc (7-22)
    """
    return tools.create_booking(token=token, court_id=court_id, date_str=date_str, start_hour=start_hour, end_hour=end_hour)


@mcp.tool()
def tool_get_my_bookings(token: str) -> list[dict]:
    """
    Lấy danh sách booking của user.
    - token: JWT của user
    """
    return tools.get_my_bookings(token=token)


@mcp.tool()
def tool_cancel_booking(token: str, booking_id: str) -> dict:
    """
    Hủy một booking.
    - token: JWT của user
    - booking_id: ID booking cần hủy
    """
    return tools.cancel_booking(token=token, booking_id=booking_id)


@mcp.tool()
def tool_cancel_booking_by_info(token: str, court_name: str, date_str: str, start_hour: int) -> dict:
    """
    Hủy booking theo tên sân, ngày và giờ bắt đầu — không cần booking_id.
    - token: JWT của user
    - court_name: tên sân (một phần cũng được, vd: "sân 2")
    - date_str: ngày, định dạng YYYY-MM-DD
    - start_hour: giờ bắt đầu (6-21)
    """
    return tools.cancel_booking_by_info(token=token, court_name=court_name, date_str=date_str, start_hour=start_hour)


if __name__ == "__main__":
    mcp.run()
