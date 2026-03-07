import { useState } from "react";
import {
  CalendarIcon,
  ClockIcon,
  EnvelopeIcon,
  PhoneIcon,
  UserIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";


function formatDateValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}


function parseDateValue(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}


function formatDisplayDate(date) {
  return date.toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}


const BookingForm = ({
  selectedTable,
  selectedDate,
  selectedTime,
  partySize,
  timeSlots,
  onDateChange,
  onTimeChange,
  onPartySizeChange,
  onSubmit,
}) => {
  const [formData, setFormData] = useState({
    customerName: "",
    phone: "",
    email: "",
    specialRequests: "",
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const handleInputChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));

    if (errors[name]) {
      setErrors((previousErrors) => ({
        ...previousErrors,
        [name]: "",
      }));
    }

    if (submitError) {
      setSubmitError("");
    }
  };

  const validateForm = () => {
    const nextErrors = {};

    if (!formData.customerName.trim()) {
      nextErrors.customerName = "Anh/chị vui lòng nhập họ tên.";
    }

    if (!formData.phone.trim()) {
      nextErrors.phone = "Anh/chị vui lòng nhập số điện thoại.";
    } else if (!/^[+]?[1-9][\d]{7,15}$/.test(formData.phone.replace(/[\s\-()]/g, ""))) {
      nextErrors.phone = "Số điện thoại chưa đúng định dạng.";
    }

    if (!formData.email.trim()) {
      nextErrors.email = "Anh/chị vui lòng nhập email.";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      nextErrors.email = "Email chưa đúng định dạng.";
    }

    if (!selectedTable) {
      nextErrors.table = "Vui lòng chọn bàn trước khi gửi booking.";
    }

    if (!selectedTime) {
      nextErrors.time = "Vui lòng chọn giờ đến.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError("");

    try {
      await onSubmit({
        ...formData,
        selectedTable,
        selectedDate,
        selectedTime,
        partySize,
      });

      setFormData({
        customerName: "",
        phone: "",
        email: "",
        specialRequests: "",
      });
    } catch (error) {
      console.error("Booking error:", error);
      const tableError = error?.response?.data?.table_id?.[0];
      setSubmitError(
        (tableError
          ? "Bàn vừa chọn không còn trống trong khung giờ này. Anh/chị vui lòng chọn bàn khác."
          : null) ||
          error?.response?.data?.party_size?.[0] ||
          error?.response?.data?.booking_date?.[0] ||
          error?.response?.data?.error ||
          error?.response?.data?.message ||
          error?.message ||
          "Không thể tạo booking. Anh/chị vui lòng thử lại."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const fieldClassName = (hasError = false) =>
    `w-full rounded-2xl border px-4 py-3 text-sm outline-none transition ${
      hasError
        ? "border-rose-300 bg-rose-50 text-rose-900"
        : "border-white/10 bg-white/[0.06] text-white placeholder:text-white/45 focus:border-[#d8b27a] focus:bg-white/10"
    }`;

  return (
    <aside className="overflow-hidden rounded-[2rem] border border-[#c29a5b]/20 bg-[linear-gradient(180deg,_#171211_0%,_#231917_55%,_#15110f_100%)] p-7 text-white shadow-[0_24px_90px_rgba(24,17,15,0.28)]">
      <div className="text-xs uppercase tracking-[0.32em] text-[#d8b27a]">
        Thông tin giữ chỗ
      </div>
      <h2 className="jp-display mt-3 text-4xl font-semibold text-[#f8ebda]">
        Hoàn tất yêu cầu đặt bàn
      </h2>
      <p className="mt-3 text-sm leading-7 text-white/70">
        Điền đủ thông tin liên hệ để nhà hàng xác nhận lại qua điện thoại hoặc email.
      </p>

      <div className="mt-6 rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-5">
        <div className="text-xs uppercase tracking-[0.28em] text-[#d8b27a]">
          Khung giờ đã chọn
        </div>
        <div className="mt-3 space-y-3 text-sm text-white/80">
          <div className="flex items-center gap-3">
            <CalendarIcon className="h-5 w-5 text-[#d8b27a]" />
            <span>{formatDisplayDate(selectedDate)}</span>
          </div>
          <div className="flex items-center gap-3">
            <ClockIcon className="h-5 w-5 text-[#d8b27a]" />
            <span>{selectedTime}</span>
          </div>
          <div className="flex items-center gap-3">
            <UsersIcon className="h-5 w-5 text-[#d8b27a]" />
            <span>{partySize} khách</span>
          </div>
        </div>

        <div className="mt-4 rounded-2xl bg-white/[0.04] px-4 py-3 text-sm text-white/80">
          {selectedTable ? (
            <div className="space-y-1">
              <div className="text-base font-semibold text-[#f8ebda]">
                Bàn T{selectedTable.id}
              </div>
              <div>
                {selectedTable.table_type} · Tầng {selectedTable.floor}
              </div>
              <div>Sức chứa tối đa {selectedTable.capacity} khách</div>
            </div>
          ) : (
            <div className="text-white/60">
              Chưa có bàn nào được chọn. Hãy chọn ở sơ đồ phía bên trái.
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="block">
            <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
              <CalendarIcon className="h-4 w-4 text-[#d8b27a]" />
              Ngày
            </span>
            <input
              type="date"
              value={formatDateValue(selectedDate)}
              min={formatDateValue(new Date())}
              onChange={(event) => onDateChange(parseDateValue(event.target.value))}
              className={fieldClassName()}
            />
          </label>

          <label className="block">
            <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
              <ClockIcon className="h-4 w-4 text-[#d8b27a]" />
              Giờ
            </span>
            <select
              value={selectedTime}
              onChange={(event) => onTimeChange(event.target.value)}
              className={fieldClassName(Boolean(errors.time))}
            >
              <option value="">Chọn giờ</option>
              {timeSlots.map((time) => (
                <option key={time} value={time} className="text-stone-900">
                  {time}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
              <UsersIcon className="h-4 w-4 text-[#d8b27a]" />
              Số khách
            </span>
            <select
              value={partySize}
              onChange={(event) => onPartySizeChange(Number(event.target.value))}
              className={fieldClassName()}
            >
              {Array.from({ length: 12 }, (_, index) => index + 1).map((size) => (
                <option key={size} value={size} className="text-stone-900">
                  {size} khách
                </option>
              ))}
            </select>
          </label>
        </div>

        {errors.table && (
          <div className="rounded-2xl border border-amber-300/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-50">
            {errors.table}
          </div>
        )}

        <div className="grid gap-4">
          <label className="block">
            <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
              <UserIcon className="h-4 w-4 text-[#d8b27a]" />
              Họ tên
            </span>
            <input
              type="text"
              name="customerName"
              value={formData.customerName}
              onChange={handleInputChange}
              placeholder="Ví dụ: Nguyễn Văn A"
              className={fieldClassName(Boolean(errors.customerName))}
            />
            {errors.customerName && (
              <p className="mt-2 text-sm text-rose-100">{errors.customerName}</p>
            )}
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
                <PhoneIcon className="h-4 w-4 text-[#d8b27a]" />
                Số điện thoại
              </span>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="0901 234 567"
                className={fieldClassName(Boolean(errors.phone))}
              />
              {errors.phone && (
                <p className="mt-2 text-sm text-rose-100">{errors.phone}</p>
              )}
            </label>

            <label className="block">
              <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
                <EnvelopeIcon className="h-4 w-4 text-[#d8b27a]" />
                Email
              </span>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="ten@email.com"
                className={fieldClassName(Boolean(errors.email))}
              />
              {errors.email && (
                <p className="mt-2 text-sm text-rose-100">{errors.email}</p>
              )}
            </label>
          </div>

          <label className="block">
            <span className="mb-2 inline-flex items-center gap-2 text-sm font-medium text-white/80">
              Ghi chú thêm
            </span>
            <textarea
              name="specialRequests"
              value={formData.specialRequests}
              onChange={handleInputChange}
              rows={4}
              placeholder="Ví dụ: cần bàn yên tĩnh, có trẻ nhỏ, sinh nhật..."
              className={fieldClassName()}
            />
          </label>
        </div>

        {submitError && (
          <div className="rounded-2xl border border-rose-300/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-50">
            {submitError}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-2xl bg-[linear-gradient(135deg,_#b78946,_#8b2328)] px-5 py-3.5 text-sm font-semibold text-white shadow-[0_16px_40px_rgba(139,35,40,0.3)] transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Đang gửi booking..." : "Gửi yêu cầu đặt bàn"}
        </button>
      </form>
    </aside>
  );
};

export default BookingForm;
