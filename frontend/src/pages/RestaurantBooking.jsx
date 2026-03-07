import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRightIcon,
  CalendarIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  HomeModernIcon,
  MapPinIcon,
  SparklesIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import BookingForm from "../components/RestaurantBooking/BookingForm.jsx";
import RestaurantLayout from "../components/RestaurantBooking/RestaurantLayout.jsx";
import TableGrid from "../components/RestaurantBooking/TableGrid.jsx";
import { restaurant as restaurantApi } from "../api";
import { BOOKING_SEARCH_PATH } from "../constants/routes.js";


const EXPERIENCE_CARDS = [
  {
    eyebrow: "Atmosphere",
    title: "Chất Nhật đương đại, ấm và riêng tư",
    body: "Tông lacquer đỏ sẫm, ánh vàng và nhịp bố cục tối giản tạo cảm giác sang nhưng không lạnh.",
  },
  {
    eyebrow: "Service",
    title: "Đặt bàn nhanh, xác nhận rõ ràng",
    body: "Khách không cần đăng nhập, chỉ cần chọn bàn phù hợp và để lại số điện thoại, email để nhà hàng phản hồi.",
  },
  {
    eyebrow: "Dining Flow",
    title: "Từ cảm hứng đến booking trong một trang",
    body: "Landing page kể câu chuyện, gợi trải nghiệm, sau đó dẫn khách xuống khu vực đặt bàn rất tự nhiên.",
  },
];

const MENU_HIGHLIGHTS = [
  {
    title: "Kuro Ember Set",
    body: "Một tổ hợp mang tinh thần yakiniku hiện đại: thịt nướng than, vị đậm, trình bày gọn và sắc.",
  },
  {
    title: "Seasonal Pairing",
    body: "Thực đơn được gợi cảm hứng từ tính mùa vụ, phù hợp cho bữa tối hẹn hò hoặc tiếp khách nhỏ.",
  },
  {
    title: "Private Corner",
    body: "Những vị trí bàn riêng tư hoặc gần cửa sổ luôn được ưu tiên cho nhóm cần không gian tốt hơn.",
  },
];

const SPACE_NOTES = [
  {
    title: "Tầng 1",
    body: "Phù hợp cho khách walk-in, cặp đôi và các buổi tối muốn vào nhịp nhanh.",
  },
  {
    title: "Không gian trong nhà",
    body: "Ánh sáng dịu, vật liệu ấm và bố cục bàn thoáng để giữ trải nghiệm dễ chịu suốt bữa ăn.",
  },
  {
    title: "Nhịp phục vụ buổi tối",
    body: "Khung 18:30 - 20:30 là thời điểm đẹp nhất để không gian lên đúng chất Nhật hiện đại.",
  },
];


function formatDateValue(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}


function normalizeTableStatus(status) {
  const mapping = {
    "Có sẵn": "available",
    "Đã đặt": "reserved",
    "Đang sử dụng": "occupied",
    "Bảo trì": "maintenance",
    Available: "available",
    Reserved: "reserved",
    Occupied: "occupied",
    Maintenance: "maintenance",
  };
  return mapping[status] || String(status || "").toLowerCase();
}


function generateTimeSlots() {
  const slots = [];
  for (let hour = 10; hour <= 21; hour += 1) {
    slots.push(`${String(hour).padStart(2, "0")}:00`);
    if (hour < 21) {
      slots.push(`${String(hour).padStart(2, "0")}:30`);
    }
  }
  return slots;
}


const RestaurantBooking = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState("19:00");
  const [partySize, setPartySize] = useState(2);
  const [selectedTable, setSelectedTable] = useState(null);
  const [floors, setFloors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const fetchTables = async () => {
      setLoading(true);
      setError("");

      try {
        const response = await restaurantApi.getTables({
          date: formatDateValue(selectedDate),
          booking_time: selectedTime,
          duration_hours: 2.0,
        });

        if (!isMounted) {
          return;
        }

        const nextFloors = (response.data || []).map((floor, index) => ({
          id: index + 1,
          name: floor.name,
          tables: (floor.tables || []).map((table) => ({
            ...table,
            status: normalizeTableStatus(table.status),
          })),
        }));

        setFloors(nextFloors);
      } catch (fetchError) {
        console.error(fetchError);
        if (isMounted) {
          setError("Không thể tải sơ đồ bàn lúc này. Anh/chị vui lòng thử lại sau.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchTables();

    return () => {
      isMounted = false;
    };
  }, [selectedDate, selectedTime]);

  useEffect(() => {
    setSelectedTable(null);
  }, [selectedDate, selectedTime, partySize]);

  useEffect(() => {
    if (!location.hash) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      document
        .getElementById(location.hash.slice(1))
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 120);

    return () => window.clearTimeout(timeoutId);
  }, [location.hash]);

  const handleTableSelect = (table) => {
    if (table.status === "available") {
      setSelectedTable(table);
    }
  };

  const handleBookingSubmit = async (formData) => {
    if (!selectedTable) {
      throw new Error("Vui lòng chọn bàn trước khi đặt.");
    }

    const payload = {
      table_id: selectedTable.id,
      guest_name: formData.customerName,
      guest_phone: formData.phone,
      guest_email: formData.email,
      notes: formData.specialRequests || "",
      party_size: partySize,
      booking_date: formatDateValue(selectedDate),
      booking_time: selectedTime,
      duration_hours: 2.0,
    };

    const response = await restaurantApi.createBooking(payload);
    const booking = response.data?.booking;

    if (!booking?.code) {
      throw new Error("Hệ thống chưa trả về mã booking.");
    }

    navigate(`${BOOKING_SEARCH_PATH}?code=${booking.code}`);
  };

  const scrollToSection = (sectionId) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const availableCount = floors.reduce(
    (sum, floor) => sum + floor.tables.filter((table) => table.status === "available").length,
    0
  );

  const timeSlots = generateTimeSlots();

  return (
    <RestaurantLayout restaurant={{ name: "PSCD Japanese Dining" }}>
      {({ openChat }) => (
        <div className="overflow-hidden">
          <section className="relative isolate px-6 pb-14 pt-8 md:px-10 md:pt-12">
            <div className="absolute left-0 top-16 h-64 w-64 rounded-full bg-[#8b2328]/10 blur-3xl"></div>
            <div className="absolute right-0 top-0 h-72 w-72 rounded-full bg-[#c29a5b]/14 blur-3xl"></div>

            <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.12fr_0.88fr]">
              <div className="relative overflow-hidden rounded-[2.7rem] border border-white/10 bg-[linear-gradient(135deg,_#15110f_0%,_#301513_58%,_#130f0d_100%)] px-8 py-10 text-white shadow-[0_40px_120px_rgba(24,17,15,0.28)] md:px-10 md:py-12">
                <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_top_right,_rgba(194,154,91,0.22),_transparent_42%)]"></div>
                <div className="relative max-w-3xl">
                  <div className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Japanese Inspired Reservation
                  </div>
                  <h1 className="jp-display mt-7 text-5xl font-semibold leading-[1.02] text-[#f8ecdd] md:text-7xl">
                    Một trang đủ đẹp để khách muốn ở lại, và đủ rõ để khách đặt bàn ngay.
                  </h1>
                  <p className="mt-6 max-w-2xl text-base leading-8 text-white/70 md:text-lg">
                    Lấy cảm hứng từ nhịp nhàng của không gian ẩm thực Nhật hiện đại:
                    tông lacquer sâu, ánh vàng dịu, câu chuyện thương hiệu rõ và hành
                    trình đặt bàn được kéo mượt từ cảm xúc sang hành động.
                  </p>

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => scrollToSection("reservation")}
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-6 py-3.5 text-sm font-semibold text-white shadow-[0_16px_40px_rgba(139,35,40,0.32)] transition hover:bg-[#a72d33]"
                    >
                      Đặt bàn ngay
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

                  <div className="mt-10 grid gap-4 sm:grid-cols-3">
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Date
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {selectedDate.toLocaleDateString("vi-VN")}
                      </div>
                    </div>
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Time
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {selectedTime}
                      </div>
                    </div>
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Tables Open
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {availableCount}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-5">
                <div className="washoku-card rounded-[2rem] p-7">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Tonight at PSCD
                      </div>
                      <h2 className="jp-display mt-3 text-3xl font-semibold text-stone-900">
                        Không gian tối nay
                      </h2>
                    </div>
                    <SparklesIcon className="h-7 w-7 text-[#b78946]" />
                  </div>
                  <div className="mt-6 space-y-4">
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <ClockIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Khung giờ đẹp</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          18:30 đến 20:30 là lúc ánh sáng, nhịp phục vụ và trải nghiệm lên tốt nhất.
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <UsersIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Nhóm khách lý tưởng</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          Từ hẹn hò 2 người đến nhóm nhỏ 6 người đều có lựa chọn chỗ ngồi phù hợp.
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <MapPinIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Điểm nhấn hành trình</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          Khách có thể khám phá câu chuyện thương hiệu, trò chuyện với AI và đặt bàn ngay trong cùng một flow.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="rounded-[2rem] border border-[#d9c6a7] bg-[linear-gradient(135deg,_#fff5eb,_#fffdf7)] p-7 shadow-[0_18px_50px_rgba(93,72,48,0.08)]">
                  <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                    Signature Direction
                  </div>
                  <h2 className="jp-display mt-3 text-3xl font-semibold text-stone-900">
                    Hướng visual mới cho guest site
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-stone-600">
                    Tách hoàn toàn guest với admin, bỏ cảm giác “ứng dụng đặt bàn thuần túy” để
                    chuyển thành landing page ẩm thực có bản sắc, chiều sâu và lực kéo đặt chỗ.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section id="story" className="px-6 py-16 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="max-w-3xl">
                <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                  About The House
                </div>
                <h2 className="jp-display mt-4 text-4xl font-semibold text-stone-900 md:text-5xl">
                  Một guest experience nên kể được câu chuyện trước khi xin khách để lại thông tin.
                </h2>
                <p className="mt-5 text-base leading-8 text-stone-600">
                  Hướng đi mới của trang guest là tạo cảm giác bước vào một nhà hàng có gu:
                  đủ gợi hình, đủ tin cậy, đủ dễ tương tác và luôn có một lối vào mềm mại sang
                  hành động đặt bàn.
                </p>
              </div>

              <div className="mt-10 grid gap-5 lg:grid-cols-3">
                {EXPERIENCE_CARDS.map((card) => (
                  <article
                    key={card.title}
                    className="washoku-card rounded-[1.9rem] p-6"
                  >
                    <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                      {card.eyebrow}
                    </div>
                    <h3 className="jp-display mt-4 text-3xl font-semibold text-stone-900">
                      {card.title}
                    </h3>
                    <p className="mt-4 text-sm leading-7 text-stone-600">{card.body}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="px-6 py-8 md:px-10">
            <div className="mx-auto max-w-7xl rounded-[2.5rem] border border-stone-200 bg-[linear-gradient(180deg,_rgba(255,250,242,0.95),_rgba(248,239,228,0.96))] px-8 py-10 shadow-[0_24px_90px_rgba(55,39,27,0.08)]">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div className="max-w-3xl">
                  <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                    Signature Mood
                  </div>
                  <h2 className="jp-display mt-4 text-4xl font-semibold text-stone-900">
                    Các mảnh ghép giúp khách muốn đặt bàn
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={openChat}
                  className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                >
                  <ChatBubbleLeftRightIcon className="h-5 w-5 text-[#8b2328]" />
                  Nhờ AI gợi ý bàn phù hợp
                </button>
              </div>

              <div className="mt-8 grid gap-5 lg:grid-cols-3">
                {MENU_HIGHLIGHTS.map((item) => (
                  <article
                    key={item.title}
                    className="rounded-[1.8rem] border border-stone-200 bg-white p-6 shadow-sm"
                  >
                    <div className="text-xs uppercase tracking-[0.24em] text-[#8b6b48]">
                      Curated Highlight
                    </div>
                    <h3 className="jp-display mt-4 text-3xl font-semibold text-stone-900">
                      {item.title}
                    </h3>
                    <p className="mt-4 text-sm leading-7 text-stone-600">{item.body}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section id="ambience" className="px-6 py-16 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-[2.4rem] border border-white/10 bg-[linear-gradient(135deg,_#211613_0%,_#120f0d_100%)] p-8 text-white shadow-[0_30px_100px_rgba(18,14,12,0.25)]">
                  <div className="text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Space & Feeling
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold leading-tight text-[#f9ebda]">
                    Không gian nên khiến khách hình dung được buổi tối của họ ngay từ header đầu tiên.
                  </h2>
                  <p className="mt-6 text-sm leading-8 text-white/70">
                    Thay vì chỉ hiển thị công cụ đặt bàn, trang guest mới tạo nhịp xem giống một
                    restaurant site thực thụ: có chất liệu, có mood, có điểm nhấn và có đích đến rõ ràng.
                  </p>
                </div>

                <div className="grid gap-5 md:grid-cols-3">
                  {SPACE_NOTES.map((item) => (
                    <article
                      key={item.title}
                      className="washoku-card rounded-[1.8rem] p-6"
                    >
                      <div className="inline-flex items-center rounded-full bg-[#f3e4d0] px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-[#8b6b48]">
                        {item.title}
                      </div>
                      <p className="mt-5 text-sm leading-7 text-stone-600">{item.body}</p>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {error && (
            <section className="px-6 pb-6 md:px-10">
              <div className="mx-auto max-w-7xl rounded-[1.75rem] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
                {error}
              </div>
            </section>
          )}

          <section id="reservation" className="px-6 pb-16 pt-4 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div className="max-w-3xl">
                  <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                    Reservation Studio
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold text-stone-900">
                    Chọn bàn và chốt booking ngay trong cùng không gian trải nghiệm
                  </h2>
                  <p className="mt-5 text-base leading-8 text-stone-600">
                    Khách có thể xem layout bàn, lọc theo ngày giờ mong muốn và gửi yêu cầu đặt bàn
                    ngay bên dưới, không bị đẩy sang một màn hình khô cứng khác.
                  </p>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={openChat}
                    className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                  >
                    <ChatBubbleLeftRightIcon className="h-5 w-5 text-[#8b2328]" />
                    Chat để tìm bàn
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate(BOOKING_SEARCH_PATH)}
                    className="inline-flex items-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                  >
                    Tra cứu booking
                    <ArrowRightIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="mt-8 grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="washoku-card rounded-[2rem] p-6">
                  <div className="flex flex-col gap-4 border-b border-stone-200 pb-5 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Live Availability
                      </div>
                      <h3 className="jp-display mt-2 text-3xl font-semibold text-stone-900">
                        Sơ đồ bàn theo ngày giờ đã chọn
                      </h3>
                    </div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-[#f7ead8] px-4 py-2 text-sm font-semibold text-[#7a5331]">
                      <HomeModernIcon className="h-5 w-5" />
                      {availableCount} bàn có thể nhận khách
                    </div>
                  </div>

                  <div className="mt-6">
                    {loading ? (
                      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white px-6 py-16 text-center text-sm text-stone-500">
                        Đang đồng bộ sơ đồ bàn theo khung giờ đã chọn...
                      </div>
                    ) : (
                      <TableGrid
                        floors={floors}
                        selectedTable={selectedTable}
                        onTableSelect={handleTableSelect}
                        partySize={partySize}
                      />
                    )}
                  </div>
                </div>

                <BookingForm
                  selectedTable={selectedTable}
                  selectedDate={selectedDate}
                  selectedTime={selectedTime}
                  partySize={partySize}
                  timeSlots={timeSlots}
                  onDateChange={setSelectedDate}
                  onTimeChange={setSelectedTime}
                  onPartySizeChange={setPartySize}
                  onSubmit={handleBookingSubmit}
                />
              </div>
            </div>
          </section>

          <section className="px-6 pb-20 md:px-10">
            <div className="mx-auto max-w-7xl rounded-[2.6rem] border border-white/10 bg-[linear-gradient(135deg,_#181311_0%,_#361615_60%,_#140f0d_100%)] px-8 py-10 text-white shadow-[0_36px_120px_rgba(18,14,12,0.28)] md:px-10">
              <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                <div>
                  <div className="text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Final Call To Action
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold text-[#f9ebda]">
                    Khách có thể nói chuyện, xem không gian, rồi đặt bàn ngay khi cảm xúc đang cao nhất.
                  </h2>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-white/70">
                    Đây là khác biệt lớn nhất của UI guest mới: thay vì đẩy khách vào một form khô,
                    toàn bộ trải nghiệm được thiết kế để tạo niềm tin, cảm giác cao cấp và động lực
                    giữ chỗ ngay trong phiên truy cập đầu tiên.
                  </p>
                </div>
                <div className="space-y-4 rounded-[2rem] border border-white/10 bg-white/[0.06] p-6">
                  <div className="flex items-start gap-3">
                    <CalendarIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Đặt bàn không cần login</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Chỉ cần bàn, họ tên, số điện thoại và email để hoàn tất yêu cầu.
                      </div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChatBubbleLeftRightIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Chatbot xuất hiện ở nhiều điểm chạm</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Header, hero và nút nổi cố định đều có thể mở concierge để hỗ trợ giữ bàn.
                      </div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <MapPinIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Tách hẳn admin khỏi guest site</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Khách sẽ không thấy cổng quản trị; admin phải vào đúng URL nội bộ mới đăng nhập được.
                      </div>
                    </div>
                  </div>
                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={openChat}
                      className="inline-flex items-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                    >
                      Mở PSCD Concierge
                      <ArrowRightIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </RestaurantLayout>
  );
};

export default RestaurantBooking;
