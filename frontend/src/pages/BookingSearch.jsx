import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowRightIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import RestaurantLayout from "../components/RestaurantBooking/RestaurantLayout.jsx";
import { restaurant as restaurantApi } from "../api";
import { GUEST_HOME_PATH } from "../constants/routes.js";


function getStatusAppearance(status) {
  const normalizedStatus = String(status || "").toUpperCase();

  const statusMap = {
    CONFIRMED: {
      label: "Đã xác nhận",
      pill: "border-emerald-200 bg-emerald-50 text-emerald-700",
      note: "Booking đã được xác nhận. Nhà hàng sẽ đón khách đúng khung giờ đã đặt.",
    },
    PENDING: {
      label: "Chờ xác nhận",
      pill: "border-amber-200 bg-amber-50 text-amber-700",
      note: "PSCD đã nhận yêu cầu và sẽ xác nhận lại qua điện thoại hoặc email.",
    },
    CANCELLED: {
      label: "Đã hủy",
      pill: "border-rose-200 bg-rose-50 text-rose-700",
      note: "Booking này đã được hủy. Anh/chị có thể tạo yêu cầu mới nếu muốn giữ chỗ lại.",
    },
    COMPLETED: {
      label: "Hoàn thành",
      pill: "border-sky-200 bg-sky-50 text-sky-700",
      note: "Booking đã hoàn tất. Cảm ơn anh/chị đã dùng bữa cùng PSCD.",
    },
    NO_SHOW: {
      label: "Không đến",
      pill: "border-stone-200 bg-stone-100 text-stone-700",
      note: "Nhà hàng ghi nhận booking không có khách đến đúng giờ đã đặt.",
    },
  };

  return statusMap[normalizedStatus] || statusMap.PENDING;
}


function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}


function formatTime(timeString) {
  return String(timeString || "").slice(0, 5);
}


const BookingSearch = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [searchCode, setSearchCode] = useState("");
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const code = searchParams.get("code");

  const runSearch = async (rawCode) => {
    const normalizedCode = rawCode.trim().toUpperCase();

    if (!normalizedCode) {
      setError("Anh/chị vui lòng nhập mã booking.");
      return;
    }

    setLoading(true);
    setError("");
    setBooking(null);

    try {
      const response = await restaurantApi.searchBookingByCode(normalizedCode);
      if (response.data) {
        setBooking(response.data);
      } else {
        setError("Không tìm thấy booking với mã này.");
      }
    } catch (searchError) {
      console.error("Error searching booking:", searchError);
      setError("Không thể tra cứu booking lúc này. Anh/chị vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!code) {
      return;
    }

    const normalizedCode = code.toUpperCase();
    setSearchCode(normalizedCode);

    const timeoutId = window.setTimeout(() => {
      runSearch(normalizedCode);
    }, 280);

    return () => window.clearTimeout(timeoutId);
  }, [code]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await runSearch(searchCode);
  };

  const statusAppearance = getStatusAppearance(booking?.status);

  return (
    <RestaurantLayout restaurant={{ name: "PSCD Japanese Dining" }}>
      {({ openChat }) => (
        <div className="px-6 pb-20 pt-10 md:px-10">
          <div className="mx-auto max-w-6xl">
            <section className="overflow-hidden rounded-[2.6rem] border border-white/10 bg-[linear-gradient(135deg,_#15110f_0%,_#301513_58%,_#130f0d_100%)] px-8 py-10 text-white shadow-[0_36px_120px_rgba(18,14,12,0.28)] md:px-10">
              <div className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
                <div>
                  <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Booking Retrieval
                  </div>
                  <h1 className="jp-display mt-6 text-5xl font-semibold leading-[1.02] text-[#f8ecdd] md:text-6xl">
                    Tra cứu trạng thái đặt bàn bằng mã booking.
                  </h1>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-white/70">
                    Sau khi gửi yêu cầu giữ bàn, khách sẽ nhận một mã booking để kiểm tra lại
                    trạng thái xác nhận bất cứ lúc nào.
                  </p>

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => navigate(`${GUEST_HOME_PATH}#reservation`)}
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                    >
                      Đặt bàn mới
                      <ArrowRightIcon className="h-5 w-5" />
                    </button>
                    <button
                      type="button"
                      onClick={openChat}
                      className="inline-flex items-center justify-center gap-2 rounded-full border border-[#d8b27a]/40 bg-white/5 px-6 py-3.5 text-sm font-semibold text-[#f6ead8] transition hover:border-[#d8b27a] hover:bg-white/10"
                    >
                      <ChatBubbleLeftRightIcon className="h-5 w-5" />
                      Chat với concierge
                    </button>
                  </div>
                </div>

                <div className="rounded-[2rem] border border-white/10 bg-white/[0.06] p-6">
                  <div className="text-xs uppercase tracking-[0.28em] text-[#d9bc94]">
                    Search Window
                  </div>
                  <form onSubmit={handleSubmit} className="mt-5 space-y-4">
                    <label className="block">
                      <span className="mb-2 block text-sm font-medium text-white/80">
                        Mã booking
                      </span>
                      <div className="flex items-center rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3">
                        <MagnifyingGlassIcon className="mr-3 h-5 w-5 text-[#d9bc94]" />
                        <input
                          type="text"
                          value={searchCode}
                          onChange={(event) => setSearchCode(event.target.value.toUpperCase())}
                          placeholder="Ví dụ: PSCD1234"
                          className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/45"
                        />
                      </div>
                    </label>

                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full rounded-2xl bg-[linear-gradient(135deg,_#b78946,_#8b2328)] px-5 py-3.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {loading ? "Đang tra cứu..." : "Tra cứu booking"}
                    </button>
                  </form>

                  <p className="mt-4 text-sm leading-7 text-white/70">
                    PSCD sẽ hiển thị ngay tình trạng xác nhận, thời gian đến và thông tin bàn tương ứng với mã booking của anh/chị.
                  </p>
                </div>
              </div>
            </section>

            {error && (
              <section className="mt-6">
                <div className="rounded-[1.75rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
                  {error}
                </div>
              </section>
            )}

            {booking && (
              <section className="mt-8 overflow-hidden rounded-[2.4rem] border border-stone-200 bg-white shadow-[0_24px_90px_rgba(55,39,27,0.08)]">
                <div className="border-b border-stone-200 bg-[linear-gradient(135deg,_#fff7eb,_#fffdf8)] px-8 py-8">
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Booking Result
                      </div>
                      <h2 className="jp-display mt-3 text-4xl font-semibold text-stone-900">
                        Mã booking {booking.code}
                      </h2>
                      <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-600">
                        {statusAppearance.note}
                      </p>
                    </div>
                    <div className={`inline-flex rounded-full border px-4 py-2 text-sm font-semibold ${statusAppearance.pill}`}>
                      {booking.status_label || statusAppearance.label}
                    </div>
                  </div>
                </div>

                <div className="grid gap-8 px-8 py-8 lg:grid-cols-[1.05fr_0.95fr]">
                  <div className="space-y-5">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-5">
                        <div className="text-sm text-stone-500">Khách đặt</div>
                        <div className="mt-2 text-xl font-semibold text-stone-900">
                          {booking.guest_name}
                        </div>
                      </div>
                      <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-5">
                        <div className="text-sm text-stone-500">Số khách</div>
                        <div className="mt-2 text-xl font-semibold text-stone-900">
                          {booking.party_size} người
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-5">
                        <div className="inline-flex items-center gap-2 text-sm text-stone-500">
                          <CalendarIcon className="h-4 w-4 text-[#8b2328]" />
                          Ngày đến
                        </div>
                        <div className="mt-2 text-lg font-semibold text-stone-900">
                          {formatDate(booking.booking_date)}
                        </div>
                      </div>
                      <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50 p-5">
                        <div className="inline-flex items-center gap-2 text-sm text-stone-500">
                          <ClockIcon className="h-4 w-4 text-[#8b2328]" />
                          Giờ đến
                        </div>
                        <div className="mt-2 text-lg font-semibold text-stone-900">
                          {formatTime(booking.booking_time)}
                        </div>
                      </div>
                    </div>

                    <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <div className="text-sm text-stone-500">Số điện thoại</div>
                          <div className="mt-2 text-base font-semibold text-stone-900">
                            {booking.guest_phone}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-stone-500">Email</div>
                          <div className="mt-2 text-base font-semibold text-stone-900">
                            {booking.guest_email}
                          </div>
                        </div>
                      </div>
                    </div>

                    {booking.notes && (
                      <div className="rounded-[1.75rem] border border-stone-200 bg-[#fff8ef] p-6">
                        <div className="text-sm font-semibold text-stone-900">Ghi chú từ khách</div>
                        <p className="mt-3 text-sm leading-7 text-stone-600">{booking.notes}</p>
                      </div>
                    )}

                    {booking.cancellation_reason && (
                      <div className="rounded-[1.75rem] border border-rose-200 bg-rose-50 p-6">
                        <div className="text-sm font-semibold text-rose-700">Lý do hủy</div>
                        <p className="mt-3 text-sm leading-7 text-rose-600">
                          {booking.cancellation_reason}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="space-y-5">
                    <div className="rounded-[2rem] border border-[#d9c6a7] bg-[linear-gradient(135deg,_#fff5eb,_#fffdf7)] p-6 shadow-[0_18px_50px_rgba(93,72,48,0.08)]">
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Seating
                      </div>
                      <h3 className="jp-display mt-3 text-3xl font-semibold text-stone-900">
                        Bàn T{booking.table_id}
                      </h3>
                      <div className="mt-5 space-y-3 text-sm text-stone-600">
                        <div className="flex items-start gap-3">
                          <UsersIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                          <span>{booking.table_type_label || booking.table_type}</span>
                        </div>
                        <div className="flex items-start gap-3">
                          <MapPinIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                          <span>Tầng {booking.table_floor}</span>
                        </div>
                        <div className="flex items-start gap-3">
                          <ClockIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                          <span>Thời lượng giữ bàn {booking.duration_hours} giờ</span>
                        </div>
                      </div>
                    </div>

                    <div className="rounded-[2rem] border border-stone-200 bg-stone-50 p-6">
                      <div className="text-sm font-semibold text-stone-900">Cần hỗ trợ thêm?</div>
                      <p className="mt-3 text-sm leading-7 text-stone-600">
                        Anh/chị có thể mở concierge để hỏi lại tình trạng bàn trống, đổi kế hoạch đặt bàn
                        hoặc nhờ PSCD gợi ý khung giờ khác phù hợp hơn.
                      </p>
                      <div className="mt-5 flex flex-col gap-3">
                        <button
                          type="button"
                          onClick={openChat}
                          className="inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                        >
                          <ChatBubbleLeftRightIcon className="h-5 w-5" />
                          Chat với concierge
                        </button>
                        <button
                          type="button"
                          onClick={() => navigate(`${GUEST_HOME_PATH}#reservation`)}
                          className="inline-flex items-center justify-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                        >
                          Đặt bàn khác
                          <ArrowRightIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </RestaurantLayout>
  );
};

export default BookingSearch;
