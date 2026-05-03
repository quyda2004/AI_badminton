from mcp.server.fastmcp import FastMCP
from .implementations import (
    get_courts,
    check_availability,
    create_booking,
    get_my_bookings,
    cancel_booking,
    cancel_booking_by_info,
)

mcp = FastMCP("Badminton Tools")


@mcp.tool()
def tool_get_courts() -> list[dict]:
    """Lấy danh sách tất cả sân cầu lông đang hoạt động."""
    return get_courts()


@mcp.tool()
def tool_check_availability(court_id: str, date_str: str) -> list[dict]:
    """
    Kiểm tra slot giờ trống của 1 sân theo ngày.
    - court_id: ID của sân
    - date_str: ngày cần kiểm tra, định dạng YYYY-MM-DD
    """
    return check_availability(court_id, date_str)


@mcp.tool()
def tool_create_booking(user_id: str, court_id: str, date_str: str, start_hour: int, end_hour: int) -> dict:
    """
    Đặt sân cho user.
    - user_id: ID user từ PostgreSQL
    - court_id: ID sân
    - date_str: ngày đặt, định dạng YYYY-MM-DD
    - start_hour: giờ bắt đầu (6-21)
    - end_hour: giờ kết thúc (7-22)
    """
    return create_booking(user_id, court_id, date_str, start_hour, end_hour)


@mcp.tool()
def tool_get_my_bookings(user_id: str) -> list[dict]:
    """
    Lấy danh sách booking của user.
    - user_id: ID user từ PostgreSQL
    """
    return get_my_bookings(user_id)


@mcp.tool()
def tool_cancel_booking(user_id: str, booking_id: str) -> dict:
    """
    Hủy một booking.
    - user_id: ID user từ PostgreSQL
    - booking_id: ID booking cần hủy
    """
    return cancel_booking(user_id, booking_id)


@mcp.tool()
def tool_cancel_booking_by_info(user_id: str, court_name: str, date_str: str, start_hour: int) -> dict:
    """
    Hủy booking theo tên sân, ngày và giờ bắt đầu — không cần booking_id.
    - user_id: ID user từ PostgreSQL
    - court_name: tên sân (một phần cũng được, vd: "sân 2")
    - date_str: ngày, định dạng YYYY-MM-DD
    - start_hour: giờ bắt đầu (6-21)
    """
    return cancel_booking_by_info(user_id, court_name, date_str, start_hour)


if __name__ == "__main__":
    mcp.run()
