import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Bars3Icon,
  ChatBubbleLeftRightIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import {
  BOOKING_SEARCH_PATH,
  GUEST_HOME_PATH,
} from "../../constants/routes.js";


const navItems = [
  { label: "Câu chuyện", type: "section", id: "story" },
  { label: "Không gian", type: "section", id: "ambience" },
  { label: "Đặt bàn", type: "section", id: "reservation" },
  { label: "Tra cứu booking", type: "route", path: BOOKING_SEARCH_PATH },
];


const RestaurantHeader = ({ onOpenChat }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const handleNavigate = (path) => {
    navigate(path);
    setIsOpen(false);
  };

  const handleSectionNavigate = (sectionId) => {
    setIsOpen(false);

    const sectionElement = document.getElementById(sectionId);
    const isGuestPage =
      location.pathname === "/" || location.pathname === GUEST_HOME_PATH;

    if (isGuestPage && sectionElement) {
      sectionElement.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    navigate(`${GUEST_HOME_PATH}#${sectionId}`);
  };

  const handleNavItemClick = (item) => {
    if (item.type === "section") {
      handleSectionNavigate(item.id);
      return;
    }

    handleNavigate(item.path);
  };

  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-white/10 bg-[rgba(18,14,12,0.84)] backdrop-blur-xl">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={() => handleNavigate(GUEST_HOME_PATH)}
          className="flex items-center gap-3 text-left"
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#c29a5b]/30 bg-[linear-gradient(145deg,_#7b1f24,_#281715)] text-sm font-bold text-[#f7ecda] shadow-[0_10px_30px_rgba(128,41,38,0.35)]">
            PS
          </div>
          <div>
            <div className="jp-display text-xl font-semibold text-[#f6ebdc]">
              PSCD Japanese Dining
            </div>
            <div className="text-[11px] uppercase tracking-[0.32em] text-[#d8c0a0]">
              Charcoal House
            </div>
          </div>
        </button>

        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => handleNavItemClick(item)}
              className="rounded-full px-4 py-2 text-sm font-medium text-[#eadbc9] transition hover:bg-white/10 hover:text-white"
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <button
            type="button"
            onClick={onOpenChat}
            className="inline-flex items-center gap-2 rounded-full border border-[#c29a5b]/40 bg-white/5 px-4 py-2 text-sm font-semibold text-[#f5e6d1] transition hover:border-[#d8b27a] hover:bg-white/10"
          >
            <ChatBubbleLeftRightIcon className="h-5 w-5" />
            Chat đặt bàn
          </button>
          <button
            type="button"
            onClick={() => handleSectionNavigate("reservation")}
            className="rounded-full bg-[#8b2328] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(139,35,40,0.35)] transition hover:bg-[#a72d33]"
          >
            Giữ bàn ngay
          </button>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="rounded-2xl border border-white/10 bg-white/5 p-2 text-[#f5e6d1] md:hidden"
        >
          {isOpen ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
        </button>
      </div>

      {isOpen && (
        <div className="border-t border-white/10 bg-[#120e0c] px-4 py-4 md:hidden">
          <div className="flex flex-col gap-2">
            {navItems.map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={() => handleNavItemClick(item)}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm font-medium text-[#f3e5d2]"
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                onOpenChat?.();
              }}
              className="rounded-2xl border border-[#c29a5b]/30 bg-[#8b2328] px-4 py-3 text-left text-sm font-semibold text-white"
            >
              Chat đặt bàn
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default RestaurantHeader;
