from typing import Optional, List, Any

from restaurant_booking.agents.io_models.input import (
    TableSearchInput,
    TableIdInput,
    BookingEntity,
)
from restaurant_booking.models import Table, Booking
from langchain_core.tools import StructuredTool
from restaurant_booking.services.availability import (
    BookingValidationError,
    TABLE_CONFLICT_MESSAGE,
    create_pending_booking,
    get_available_tables,
)
from restaurant_booking.services.public_links import build_booking_search_url


class TablesService:

    def _search_tables(
        self,
        booking_date: str = None,
        booking_time: str = None,
        table_type: str = None,
        party_size: int = None,
        floor: int = None,
        table_id: Optional[int] = None,
    ) -> str:
        """
        Tìm kiếm các bàn trống phù hợp với yêu cầu đặt bàn.
        """
        try:
            error = self.validate_search_tables_info(booking_date, booking_time, table_type, party_size, floor)
            if error:
                return error

            available_tables = get_available_tables(
                booking_date=booking_date,
                booking_time=booking_time,
                table_type=table_type,
                party_size=party_size,
                floor=floor,
                table_id=table_id,
                duration_hours=2.0,
            )

            # Prepare result
            result = []
            for table in available_tables:
                result.append(
                    {
                        "table_id": table.id,
                        "table_type": table.get_table_type_display(),
                        "capacity": table.capacity,
                        "floor": table.floor,
                        "status": table.get_status_display(),
                        "notes": table.notes or "",
                    }
                )

            if not result:
                return "Không tìm thấy bàn phù hợp với yêu cầu của bạn."

            return result

        except Exception as e:
            return f"Lỗi khi tìm kiếm bàn: {str(e)}"

    def _get_table_by_id(self, table_id: int) -> str:
        """
        Lấy thông tin bàn theo ID.
        """
        try:
            table = Table.objects.get(id=table_id)
            result = f"""
            Thông tin bàn:
            Số: {table.id}
            Loại bàn: {table.get_table_type_display()}
            Sức chứa: {table.capacity}
            Chiều rộng: {table.width}
            Chiều dài: {table.length}
            Tầng: {table.floor}
            """
            return result
        except Exception as e:
            return f"Lỗi khi lấy thông tin bàn: {str(e)}"

    def _book_table(
        self,
        table_id: int,
        booking_date: str,
        booking_time: str,
        party_size: int,
        table_type: str,
        floor: int,
        guest_name: str,
        guest_phone: str,
        guest_email: str,
        note: str = "",
    ) -> str:
        """
        Đặt bàn.
        """
        try:
            error = self.validate_guest_info(guest_name, guest_phone, guest_email, note)
            if error:
                return error

            booking = create_pending_booking(
                table_id=table_id,
                guest_name=guest_name,
                guest_phone=guest_phone,
                guest_email=guest_email,
                booking_date=booking_date,
                booking_time=booking_time,
                party_size=party_size,
                duration_hours=2.0,
                notes=note,
                source=Booking.BookingSource.WEBSITE,
            )

        except BookingValidationError as e:
            error_message = e.detail.get("table_id") or e.detail.get("booking_time") or e.detail.get("booking_date")
            if error_message == TABLE_CONFLICT_MESSAGE:
                return (
                    f"Bàn số {table_id} vừa được khách khác giữ chỗ ở khung giờ này. "
                    "Anh/chị vui lòng chọn bàn khác để PSCD hỗ trợ tiếp ạ."
                )
            return str(error_message or e.detail)
        except Exception as e:
            return f"Lỗi khi đặt bàn: {str(e)}"

        lookup_url = build_booking_search_url(booking.code)
        return f"PSCD đã ghi nhận yêu cầu đặt bàn thành công. Mã đặt bàn: {booking.code}. Thông tin xác nhận đã được gửi tới email của anh/chị. Bạn có thể tra cứu thông tin đặt bàn tại đây: {lookup_url}"

    def _summary_booking_info(
        self, 
        table_id: int = None,
        booking_date: str = None,
        booking_time: str = None,
        party_size: int = None,
        table_type: str = None,
        floor: int = None,
        guest_name: str = None,
        guest_phone: str = None,
        guest_email: str = None,
        note: str = None
    ) -> str:
        """
        Summary booking information.
        """
        return f"""Em xin xác nhận lại thông tin đặt bàn:
        Thông tin đặt bàn:
        Bàn số: {table_id}
        Ngày đặt bàn: {booking_date}
        Giờ đặt bàn: {booking_time}
        Số lượng người: {party_size}
        Loại bàn: {table_type}
        Tầng: {floor}
        Tên khách: {guest_name}
        Số điện thoại: {guest_phone}
        Email: {guest_email}
        Ghi chú: {note}
        Anh/chị vui lòng xác nhận thông tin trên đã đúng chưa ạ?
        """

    def validate_guest_info(self, guest_name: str, guest_phone: str, guest_email: str, note: str = None) -> str:
        """
        Validate guest information.
        """
        if not guest_name or not guest_phone or not guest_email:
            return "Hỏi thông tin: guest_name, guest_phone và guest_email của khách hàng."
        if note is None:
            return f"Hỏi thông tin: note của khách hàng."
        return None

    def validate_search_tables_info(self, booking_date: str, booking_time: str, table_type: str, party_size: int, floor: int) -> str:
        """
        Validate table information.
        """
        if not booking_date and not booking_time:
            return f"Hỏi thông tin: booking_date và booking_time của khách hàng."
        if not booking_date:
            return f"Hỏi thông tin: booking_date của khách hàng."
        if not booking_time:
            return f"Hỏi thông tin: booking_time của khách hàng."
        if not table_type:
            return f"Hỏi thông tin: table_type của khách hàng."
        if not party_size:
            return f"Hỏi thông tin: party_size của khách hàng."
        if not floor:
            return f"Hỏi thông tin: floor của khách hàng."
        return None

    def create_tools(self) -> List[Any]:
        return [
            StructuredTool.from_function(
                func=self._search_tables,
                name="search_tables",
                description=(
                    """Tìm kiếm các bàn trống phù hợp với yêu cầu đặt bàn.
                    Nhận vào: 
                    booking_date: Ngày đặt bàn (YYYY-MM-DD),
                    booking_time: Giờ đặt bàn (HH:MM), 
                    table_type: Loại bàn,
                    party_size: Số người, 
                    floor: Tầng, 
                    table_id: ID bàn (tùy chọn).
                    Trả về danh sách bàn phù hợp hoặc thông báo nếu không có bàn.
                    Chỉ được gọi khi tất cả tham số đã được cung cấp rõ ràng từ người dùng. Không được tự suy đoán hoặc sử dụng giá trị mặc định
                    """
                ),
                args_schema=TableSearchInput,
            ),
            StructuredTool.from_function(
                func=self._book_table,
                name="book_table",
                description=(
                    """Đặt bàn.
                    Nhận vào: 
                    table_id (ID của bàn),
                    booking_date (YYYY-MM-DD), 
                    booking_time (HH:MM), 
                    party_size (số lượng người), 
                    guest_name (tên khách hàng), 
                    guest_phone (số điện thoại khách hàng),
                    guest_email (email khách hàng),
                    note (ghi chú của khách hàng).
                    Trả về thông báo thành công hoặc thông báo lỗi.
                    """
                ),
                args_schema=BookingEntity,
            ),
            StructuredTool.from_function(
                func=self._get_table_by_id,
                name="get_table_by_id",
                description=(
                    """Lấy thông tin bàn theo ID.
                    Nhận vào: table_id (ID của bàn).
                    Trả về thông tin bàn.
                    """
                ),
                args_schema=TableIdInput,
            ),
            StructuredTool.from_function(
                func=self._summary_booking_info,
                name="summary_booking_info",
                description=(
                    """Tóm tắt thông tin đặt bàn và yêu cầu xác nhận.
                    Nhận vào: table_id (ID của bàn),
                    booking_date (YYYY-MM-DD),
                    booking_time (HH:MM),
                    party_size (số lượng người),
                    table_type (loại bàn),
                    floor (tầng),
                    guest_name (tên khách hàng),
                    guest_phone (số điện thoại khách hàng),
                    note (ghi chú của khách hàng).
                    Trả về thông tin đặt bàn và yêu cầu xác nhận.
                    """
                ),
                args_schema=BookingEntity,
            ),
        ]
