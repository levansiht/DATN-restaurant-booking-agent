import { startTransition, useEffect, useRef, useState } from "react";
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
import MenuExplorerSection from "../components/RestaurantBooking/MenuExplorerSection.jsx";
import RestaurantLayout from "../components/RestaurantBooking/RestaurantLayout.jsx";
import TableGrid from "../components/RestaurantBooking/TableGrid.jsx";
import { restaurant as restaurantApi } from "../api";
import { BOOKING_SEARCH_PATH } from "../constants/routes.js";
import {
  publishRestaurantRealtimeEvent,
  useRestaurantRealtime,
} from "../hooks/useRestaurantRealtime.js";


const EXPERIENCE_CARDS = [
  {
    eyebrow: "Bếp than",
    title: "Thơm lửa, đậm vị và gọn gàng khi gọi món",
    body: "Các set nướng được cân bằng giữa phần thịt, rau cuốn và sốt house để bữa tối vừa tròn vị vừa dễ chia sẻ.",
  },
  {
    eyebrow: "Không gian",
    title: "Ấm cúng cho hẹn hò, đủ riêng cho buổi gặp quan trọng",
    body: "Ánh đèn vàng, bàn ngồi thoải mái và khoảng cách hợp lý giúp PSCD phù hợp cho cặp đôi lẫn nhóm nhỏ cần sự riêng tư.",
  },
  {
    eyebrow: "Giữ chỗ",
    title: "Đặt bàn nhanh trước khung giờ đẹp",
    body: "Chọn ngày, giờ và vị trí phù hợp trong vài bước để không phải chờ bàn khi quán vào nhịp đông nhất buổi tối.",
  },
];

const SPACE_NOTES = [
  {
    title: "Bàn hẹn hò",
    body: "Khu bàn 2 người có ánh sáng dịu và khoảng riêng vừa đủ để giữ cuộc trò chuyện thoải mái suốt bữa tối.",
  },
  {
    title: "Nhóm nhỏ 4 - 6 người",
    body: "Các cụm bàn rộng rãi phù hợp cho gặp gỡ bạn bè, sinh nhật nhỏ hoặc buổi tối tiếp khách không quá hình thức.",
  },
  {
    title: "Khung giờ đẹp",
    body: "Từ 18:30 đến 20:30 là lúc ánh đèn, nhịp phục vụ và không khí quán lên tròn nhất nên bàn đẹp thường kín sớm.",
  },
];

const OCCASION_TAGS = ["Hẹn hò buổi tối", "Sinh nhật nhỏ", "Tiếp khách"];
const KITCHEN_TAGS = ["Bếp than", "Sốt house", "Bàn riêng"];

const DEFAULT_RESTAURANT = {
  name: "PSCD Japanese Dining",
  description: "",
  public_booking_fee_amount: 100000,
  chatbot_booking_fee_amount: 100000,
};


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


function formatCurrency(value) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}


const RestaurantBooking = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [restaurantProfile, setRestaurantProfile] = useState(DEFAULT_RESTAURANT);
  const [menuCatalog, setMenuCatalog] = useState({ categories: [], items: [] });
  const [menuLoading, setMenuLoading] = useState(true);
  const [menuError, setMenuError] = useState("");
  const [selectedMenuItemIds, setSelectedMenuItemIds] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedTime, setSelectedTime] = useState("19:00");
  const [partySize, setPartySize] = useState(2);
  const [selectedTable, setSelectedTable] = useState(null);
  const [floors, setFloors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [availabilityNotice, setAvailabilityNotice] = useState("");
  const [realtimeRevision, setRealtimeRevision] = useState(0);
  const selectedTableRef = useRef(selectedTable);
  const lastVisibleSlotRef = useRef("");
  const hasCompletedInitialLoadRef = useRef(false);

  useEffect(() => {
    let isMounted = true;

    const loadCatalog = async () => {
      setMenuLoading(true);
      setMenuError("");
      try {
        const [profileResponse, menuResponse] = await Promise.all([
          restaurantApi.getRestaurantProfile(),
          restaurantApi.getMenu(),
        ]);

        if (!isMounted) {
          return;
        }

        setRestaurantProfile({
          ...DEFAULT_RESTAURANT,
          ...(profileResponse.data || {}),
        });
        setMenuCatalog({
          categories: menuResponse.data?.categories || [],
          items: menuResponse.data?.items || [],
        });
      } catch (catalogError) {
        console.error(catalogError);
        if (isMounted) {
          setMenuError("Không thể tải menu lúc này. Anh/chị vui lòng thử lại sau.");
        }
      } finally {
        if (isMounted) {
          setMenuLoading(false);
        }
      }
    };

    loadCatalog();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    selectedTableRef.current = selectedTable;
  }, [selectedTable]);

  useEffect(() => {
    let isMounted = true;
    const currentSlotKey = `${formatDateValue(selectedDate)}-${selectedTime}`;
    const shouldShowLoading =
      !hasCompletedInitialLoadRef.current || lastVisibleSlotRef.current !== currentSlotKey;

    const fetchTables = async () => {
      if (shouldShowLoading) {
        setLoading(true);
      }
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

        const currentSelectedTable = selectedTableRef.current;
        if (currentSelectedTable) {
          const refreshedSelectedTable = nextFloors
            .flatMap((floor) => floor.tables)
            .find((table) => table.id === currentSelectedTable.id);

          if (
            !refreshedSelectedTable ||
            refreshedSelectedTable.status !== "available" ||
            !refreshedSelectedTable.is_available_for_booking
          ) {
            setSelectedTable(null);
            setAvailabilityNotice(
              "Bàn anh/chị đang chọn vừa được giữ chỗ. Vui lòng chọn bàn khác phù hợp."
            );
          } else if (
            refreshedSelectedTable.status !== currentSelectedTable.status ||
            refreshedSelectedTable.floor !== currentSelectedTable.floor ||
            refreshedSelectedTable.capacity !== currentSelectedTable.capacity
          ) {
            setSelectedTable(refreshedSelectedTable);
          }
        }
      } catch (fetchError) {
        console.error(fetchError);
        if (isMounted) {
          setError("Không thể tải sơ đồ bàn lúc này. Anh/chị vui lòng thử lại sau.");
        }
      } finally {
        if (isMounted) {
          hasCompletedInitialLoadRef.current = true;
          lastVisibleSlotRef.current = currentSlotKey;
          setLoading(false);
        }
      }
    };

    fetchTables();

    return () => {
      isMounted = false;
    };
  }, [selectedDate, selectedTime, realtimeRevision]);

  useEffect(() => {
    setSelectedTable(null);
    setAvailabilityNotice("");
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
    if (table.status === "available" && table.is_available_for_booking) {
      setAvailabilityNotice("");
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

    try {
      const response = await restaurantApi.createBooking(payload);
      const booking = response.data?.booking;

      if (!booking?.code) {
        throw new Error("Hệ thống chưa trả về mã booking.");
      }

      publishRestaurantRealtimeEvent({
        type: "booking.changed",
        action: "created",
        booking_id: booking.id,
        table_id: booking.table_id,
        booking_date: booking.booking_date,
        booking_time: booking.booking_time,
        status: booking.status,
      });

      navigate(`${BOOKING_SEARCH_PATH}?code=${booking.code}`);
    } catch (submissionError) {
      const tableError = submissionError?.response?.data?.table_id?.[0];
      if (tableError) {
        setSelectedTable(null);
        setAvailabilityNotice(
          "Bàn anh/chị vừa chọn đã được khách khác giữ chỗ. Vui lòng chọn bàn khác phù hợp."
        );
        startTransition(() => {
          setRealtimeRevision((currentRevision) => currentRevision + 1);
        });
      }

      throw submissionError;
    }
  };

  const scrollToSection = (sectionId) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const toggleSelectedMenuItem = (itemId) => {
    setSelectedMenuItemIds((previousIds) =>
      previousIds.includes(itemId)
        ? previousIds.filter((currentId) => currentId !== itemId)
        : [...previousIds, itemId]
    );
  };

  const addMenuItem = (itemId) => {
    setSelectedMenuItemIds((previousIds) =>
      previousIds.includes(itemId) ? previousIds : [...previousIds, itemId]
    );
  };

  const availableCount = floors.reduce(
    (sum, floor) => sum + floor.tables.filter((table) => table.status === "available").length,
    0
  );

  const timeSlots = generateTimeSlots();

  const { isConnected: isRealtimeConnected } = useRestaurantRealtime({
    enabled: true,
    onEvent: (event) => {
      if (event?.domain !== "restaurant_booking") {
        return;
      }

      if (event.type === "booking.changed" || event.type === "table.changed") {
        startTransition(() => {
          setRealtimeRevision((currentRevision) => currentRevision + 1);
        });
      }
    },
  });

  useEffect(() => {
    if (isRealtimeConnected) {
      return undefined;
    }

    const refreshTables = () => {
      if (document.visibilityState !== "visible") {
        return;
      }

      startTransition(() => {
        setRealtimeRevision((currentRevision) => currentRevision + 1);
      });
    };

    const intervalId = window.setInterval(refreshTables, 3000);
    document.addEventListener("visibilitychange", refreshTables);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", refreshTables);
    };
  }, [isRealtimeConnected]);

  return (
    <RestaurantLayout
      restaurant={restaurantProfile}
      selectedItemIds={selectedMenuItemIds}
      onAddMenuItem={addMenuItem}
    >
      {({ openChat }) => (
        <div className="overflow-hidden">
          <section className="relative isolate px-6 pb-14 pt-8 md:px-10 md:pt-12">
            <div className="absolute left-0 top-16 h-64 w-64 rounded-full bg-[#8b2328]/10 blur-3xl"></div>
            <div className="absolute right-0 top-0 h-72 w-72 rounded-full bg-[#c29a5b]/14 blur-3xl"></div>

            <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.12fr_0.88fr]">
              <div className="hero-panel relative overflow-hidden rounded-[2.7rem] border border-white/10 bg-[linear-gradient(135deg,_#15110f_0%,_#301513_58%,_#130f0d_100%)] px-8 py-10 text-white shadow-[0_40px_120px_rgba(24,17,15,0.28)] md:px-10 md:py-12">
                <div className="rice-paper-grid"></div>
                <div className="hero-lantern hero-lantern--one"></div>
                <div className="hero-lantern hero-lantern--two"></div>
                <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_top_right,_rgba(194,154,91,0.22),_transparent_42%)]"></div>
                <div className="relative max-w-3xl">
                  <div className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Nhà hàng nướng Nhật đương đại
                  </div>
                  <h1 className="jp-display mt-7 text-5xl font-semibold leading-[1.02] text-[#f8ecdd] md:text-7xl">
                    Bàn đẹp, món nóng và một bữa tối đúng gu bắt đầu từ chỗ ngồi đúng ý.
                  </h1>
                  <p className="mt-6 max-w-2xl text-base leading-8 text-white/70 md:text-lg">
                    PSCD mang tinh thần quán ăn Nhật đương đại với món nướng thơm lửa,
                    góc ngồi ấm cúng và quy trình giữ bàn nhanh cho hẹn hò, gặp gỡ bạn bè
                    hay tiếp khách vào buổi tối.
                  </p>

                  <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                    <button
                      type="button"
                      onClick={() => scrollToSection("reservation")}
                      className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-6 py-3.5 text-sm font-semibold text-white shadow-[0_16px_40px_rgba(139,35,40,0.32)] transition hover:bg-[#a72d33]"
                    >
                      Xem bàn trống
                      <ArrowRightIcon className="h-5 w-5" />
                    </button>
                    <button
                      type="button"
                      onClick={openChat}
                      className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full border border-[#d8b27a]/40 bg-white/5 px-6 py-3.5 text-sm font-semibold text-[#f6ead8] transition hover:border-[#d8b27a] hover:bg-white/10"
                    >
                      <ChatBubbleLeftRightIcon className="h-5 w-5" />
                      Nhờ tư vấn chỗ ngồi
                    </button>
                  </div>

                  <div className="mt-10 grid gap-4 sm:grid-cols-3">
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4 backdrop-blur-sm">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Ngày ghé quán
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {selectedDate.toLocaleDateString("vi-VN")}
                      </div>
                    </div>
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4 backdrop-blur-sm">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Khung giờ
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {selectedTime}
                      </div>
                    </div>
                    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.06] p-4 backdrop-blur-sm">
                      <div className="text-xs uppercase tracking-[0.24em] text-[#d9bc94]">
                        Bàn còn trống
                      </div>
                      <div className="mt-3 text-xl font-semibold text-[#f8ecdd]">
                        {availableCount}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-5">
                <div className="washoku-card floating-card rounded-[2rem] p-7">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Nhịp quán tối nay
                      </div>
                      <h2 className="jp-display mt-3 text-3xl font-semibold text-stone-900">
                        Bếp đang vào nhịp đẹp nhất
                      </h2>
                    </div>
                    <SparklesIcon className="h-7 w-7 text-[#b78946]" />
                  </div>
                  <div className="mt-6 space-y-4">
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <ClockIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Khung giờ dễ lên bàn</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          18:30 đến 20:30 là lúc món lên đều, ánh đèn đẹp và không khí quán tròn vị nhất.
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <UsersIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Dịp phù hợp</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          Từ hẹn hò 2 người đến nhóm 6 người đều có khu vực ngồi phù hợp và dễ trò chuyện.
                        </div>
                      </div>
                    </div>
                    <div className="flex items-start gap-3 rounded-[1.4rem] bg-white px-4 py-4 shadow-sm">
                      <MapPinIcon className="mt-0.5 h-5 w-5 text-[#8b2328]" />
                      <div>
                        <div className="text-sm font-semibold text-stone-900">Trải nghiệm đáng nhớ</div>
                        <div className="mt-1 text-sm leading-6 text-stone-600">
                          Giữ được đúng chỗ ngồi, đến quán đúng giờ và bắt đầu bữa tối ngay khi vừa bước vào.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="steam-showcase mt-6 rounded-[1.6rem] border border-[#ecd8b8] bg-[linear-gradient(180deg,_#fffaf3,_#f7ebd8)] p-4">
                    <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-[0.22em] text-[#8b6b48]">
                      <span>Bếp than hôm nay</span>
                      <span className="status-ember">Đang lên lửa</span>
                    </div>
                    <div className="steam-platter mt-4">
                      <span className="steam-line"></span>
                      <span className="steam-line"></span>
                      <span className="steam-line"></span>
                      <div className="dish-core"></div>
                    </div>
                    <div className="mt-5 flex flex-wrap gap-2">
                      {KITCHEN_TAGS.map((tag) => (
                        <span key={tag} className="lantern-chip">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="rounded-[2rem] border border-[#d9c6a7] bg-[linear-gradient(135deg,_#fff5eb,_#fffdf7)] p-7 shadow-[0_18px_50px_rgba(93,72,48,0.08)]">
                  <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                    Lý do khách giữ bàn sớm
                  </div>
                  <h2 className="jp-display mt-3 text-3xl font-semibold text-stone-900">
                    Đi sớm một nhịp, ngon hơn một nhịp
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-stone-600">
                    Bàn đẹp trong khung 18:30 đến 20:30 thường kín nhanh. Giữ chỗ sớm giúp
                    chọn đúng góc ngồi, chủ động cho hẹn hò, sinh nhật nhỏ và không phải đợi bàn.
                  </p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {OCCASION_TAGS.map((tag) => (
                      <span key={tag} className="lantern-chip">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section id="story" className="px-6 py-16 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="max-w-3xl">
                <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                  Câu chuyện PSCD
                </div>
                <h2 className="jp-display mt-4 text-4xl font-semibold text-stone-900 md:text-5xl">
                  Một quán ăn thuyết phục bằng mùi vị, không gian và cảm giác được chờ đón.
                </h2>
                <p className="mt-5 text-base leading-8 text-stone-600">
                  Từ lúc lướt trang đến khi ngồi vào bàn, mọi điểm chạm đều nên kể đúng câu
                  chuyện của quán: đồ ăn có cá tính, không gian có gu và việc giữ chỗ đủ nhanh
                  để khách dễ dàng ra quyết định.
                </p>
              </div>

              <div className="mt-10 grid gap-5 lg:grid-cols-3">
                {EXPERIENCE_CARDS.map((card) => (
                  <article
                    key={card.title}
                    className="washoku-card menu-card rounded-[1.9rem] p-6"
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

          <MenuExplorerSection
            restaurantName={restaurantProfile.name}
            categories={menuCatalog.categories}
            items={menuCatalog.items}
            loading={menuLoading}
            selectedItemIds={selectedMenuItemIds}
            onAddItem={toggleSelectedMenuItem}
            onBookNow={() => scrollToSection("reservation")}
            onOpenChat={openChat}
          />

          {menuError ? (
            <section className="px-6 pb-6 md:px-10">
              <div className="mx-auto max-w-7xl rounded-[1.75rem] border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
                {menuError}
              </div>
            </section>
          ) : null}

          <section id="ambience" className="px-6 py-16 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-[2.4rem] border border-white/10 bg-[linear-gradient(135deg,_#211613_0%,_#120f0d_100%)] p-8 text-white shadow-[0_30px_100px_rgba(18,14,12,0.25)]">
                  <div className="text-xs uppercase tracking-[0.32em] text-[#d9bc94]">
                    Không gian & cảm xúc
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold leading-tight text-[#f9ebda]">
                    Mỗi khu vực ngồi đều phục vụ một kiểu bữa tối khác nhau.
                  </h2>
                  <p className="mt-6 text-sm leading-8 text-white/70">
                    Có bàn cho cặp đôi muốn riêng tư, nhóm bạn cần không khí rôm rả và những
                    khung giờ đẹp để món ăn lên bàn vừa đúng lúc, tròn vị lẫn cảm xúc.
                  </p>
                </div>

                <div className="grid gap-5 md:grid-cols-3">
                  {SPACE_NOTES.map((item) => (
                    <article
                      key={item.title}
                      className="washoku-card menu-card rounded-[1.8rem] p-6"
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

          {availabilityNotice && (
            <section className="px-6 pb-6 md:px-10">
              <div className="mx-auto max-w-7xl rounded-[1.75rem] border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
                {availabilityNotice}
              </div>
            </section>
          )}

          <section id="reservation" className="px-6 pb-16 pt-4 md:px-10">
            <div className="mx-auto max-w-7xl">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div className="max-w-3xl">
                  <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                    Đặt chỗ trực tuyến
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold text-stone-900">
                    Chọn khung giờ, chọn bàn và giữ chỗ trước khi quán vào giờ đông
                  </h2>
                  <p className="mt-5 text-base leading-8 text-stone-600">
                    Xem bàn trống theo thời gian thực, lọc theo số khách và gửi yêu cầu đặt chỗ
                    ngay trên trang. Quy trình ngắn, rõ và đúng với nhu cầu của một quán ăn.
                  </p>
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={openChat}
                    className="cta-sheen inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                  >
                    <ChatBubbleLeftRightIcon className="h-5 w-5 text-[#8b2328]" />
                    Nhờ tư vấn chọn bàn
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate(BOOKING_SEARCH_PATH)}
                    className="cta-sheen inline-flex items-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                  >
                    Tra cứu mã đặt bàn
                    <ArrowRightIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="mt-8 grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="washoku-card rounded-[2rem] p-6">
                  <div className="flex flex-col gap-4 border-b border-stone-200 pb-5 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                        Bàn trống theo thời gian thực
                      </div>
                      <h3 className="jp-display mt-2 text-3xl font-semibold text-stone-900">
                        Sơ đồ chỗ ngồi theo ngày giờ đã chọn
                      </h3>
                    </div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-[#f7ead8] px-4 py-2 text-sm font-semibold text-[#7a5331]">
                      <HomeModernIcon className="h-5 w-5" />
                      {availableCount} bàn sẵn sàng phục vụ
                    </div>
                  </div>

                  <div className="mt-6">
                    {loading ? (
                      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white px-6 py-16 text-center text-sm text-stone-500">
                        Đang cập nhật sơ đồ bàn theo khung giờ đã chọn...
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
                  bookingFeeAmount={restaurantProfile.public_booking_fee_amount}
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
                    Giữ bàn trước giờ đẹp
                  </div>
                  <h2 className="jp-display mt-4 text-5xl font-semibold text-[#f9ebda]">
                    Chọn chỗ ngồi đẹp trước khi quán kín bàn vào buổi tối.
                  </h2>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-white/70">
                    Nếu đã có sẵn ngày và khung giờ mong muốn, đây là lúc tốt nhất để giữ chỗ.
                    PSCD sẽ xác nhận nhanh để anh/chị yên tâm lên lịch cho bữa tối, hẹn hò
                    hoặc buổi gặp mặt quan trọng.
                  </p>
                </div>
                <div className="space-y-4 rounded-[2rem] border border-white/10 bg-white/[0.06] p-6">
                  <div className="flex items-start gap-3">
                    <CalendarIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Đặt chỗ không cần tạo tài khoản</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Chỉ cần chọn bàn, để lại thông tin liên hệ và gửi yêu cầu trong vài bước ngắn.
                      </div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <ChatBubbleLeftRightIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Tư vấn chọn bàn nhanh qua chat</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Nếu cần góc riêng, bàn gần cửa sổ hoặc chỗ ngồi cho nhóm, quầy tư vấn có thể hỗ trợ ngay.
                      </div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <MapPinIcon className="mt-1 h-5 w-5 text-[#d9bc94]" />
                    <div>
                      <div className="text-sm font-semibold text-[#f7ebda]">Hợp cho hẹn hò, sinh nhật và gặp gỡ bạn bè</div>
                      <div className="mt-1 text-sm leading-7 text-white/70">
                        Mọi nhu cầu từ bữa tối 2 người đến nhóm nhỏ đều có loại bàn và khung giờ phù hợp.
                      </div>
                    </div>
                  </div>
                  <div className="pt-2">
                    <button
                      type="button"
                      onClick={openChat}
                      className="cta-sheen inline-flex items-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                    >
                      Giữ bàn với PSCD
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
