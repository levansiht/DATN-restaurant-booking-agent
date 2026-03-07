import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRightIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  MapPinIcon,
} from "@heroicons/react/24/outline";
import {
  BOOKING_SEARCH_PATH,
  GUEST_HOME_PATH,
} from "../../constants/routes.js";


const footerSections = [
  { label: "Câu chuyện", id: "story" },
  { label: "Không gian", id: "ambience" },
  { label: "Đặt chỗ", id: "reservation" },
];


const RestaurantFooter = ({ restaurant, onOpenChat }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleSectionNavigate = (sectionId) => {
    const sectionElement = document.getElementById(sectionId);
    const isRestaurantPage =
      location.pathname === "/" || location.pathname === GUEST_HOME_PATH;

    if (isRestaurantPage && sectionElement) {
      sectionElement.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    navigate(`${GUEST_HOME_PATH}#${sectionId}`);
  };

  return (
    <footer className="restaurant-footer relative overflow-hidden border-t border-white/10">
      <div className="absolute left-0 top-0 h-52 w-52 rounded-full bg-[#8b2328]/16 blur-3xl"></div>
      <div className="absolute bottom-0 right-0 h-56 w-56 rounded-full bg-[#c29a5b]/18 blur-3xl"></div>

      <div className="relative mx-auto max-w-7xl px-6 pb-10 pt-12 md:px-10">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.8fr_0.9fr]">
          <div>
            <button
              type="button"
              onClick={() => navigate(GUEST_HOME_PATH)}
              className="flex items-center gap-3 text-left"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#c29a5b]/30 bg-[linear-gradient(145deg,_#7b1f24,_#281715)] text-sm font-bold text-[#f7ecda] shadow-[0_10px_30px_rgba(128,41,38,0.35)]">
                PS
              </div>
              <div>
                <div className="jp-display text-2xl font-semibold text-[#f6ebdc]">
                  {restaurant?.name || "PSCD Japanese Dining"}
                </div>
                <div className="text-[11px] uppercase tracking-[0.32em] text-[#d8c0a0]">
                  Charcoal House
                </div>
              </div>
            </button>

            <p className="mt-5 max-w-xl text-sm leading-7 text-white/70">
              Một bữa tối ngon bắt đầu từ đúng chỗ ngồi, đúng khung giờ và đúng cảm xúc.
              PSCD luôn để sẵn các lối vào nhanh để anh/chị xem không gian, chọn bàn phù hợp
              và giữ chỗ ngay khi đã có lịch hẹn.
            </p>

            <div className="mt-5 flex flex-wrap gap-2">
              {["Bếp than", "Bàn đẹp", "Giữ chỗ nhanh"].map((tag) => (
                <span key={tag} className="footer-chip">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-[#d8b27a]">
              Khám phá nhanh
            </div>
            <div className="mt-5 flex flex-col gap-3">
              {footerSections.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleSectionNavigate(item.id)}
                  className="footer-link"
                >
                  <span>{item.label}</span>
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
              ))}
              <button
                type="button"
                onClick={() => navigate(BOOKING_SEARCH_PATH)}
                className="footer-link"
              >
                <span>Tra cứu mã đặt bàn</span>
                <ArrowRightIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-[1.8rem] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <ClockIcon className="mt-1 h-5 w-5 text-[#d8b27a]" />
                <div>
                  <div className="text-sm font-semibold text-[#f7ebda]">
                    Giờ nhận giữ bàn
                  </div>
                  <div className="mt-1 text-sm leading-7 text-white/70">
                    Hệ thống nhận yêu cầu giữ chỗ từ 10:00 đến 21:00, đẹp nhất vẫn là khung 18:30 - 20:30.
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-[1.8rem] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <MapPinIcon className="mt-1 h-5 w-5 text-[#d8b27a]" />
                <div>
                  <div className="text-sm font-semibold text-[#f7ebda]">
                    Trải nghiệm tại quán
                  </div>
                  <div className="mt-1 text-sm leading-7 text-white/70">
                    Hợp cho hẹn hò, sinh nhật nhỏ, tiếp khách và những buổi tối cần một bàn ngồi đủ đẹp để bắt đầu câu chuyện.
                  </div>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onOpenChat}
              className="cta-sheen inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#8b2328] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
            >
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
              Chat để giữ bàn ngay
            </button>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-white/10 pt-6 text-sm text-white/55 md:flex-row md:items-center md:justify-between">
          <div>{restaurant?.name || "PSCD Japanese Dining"} · Charcoal House</div>
          <div>Món nướng thơm lửa, bàn đẹp giữ sớm và một bữa tối được chuẩn bị đúng nhịp.</div>
        </div>
      </div>
    </footer>
  );
};

export default RestaurantFooter;
