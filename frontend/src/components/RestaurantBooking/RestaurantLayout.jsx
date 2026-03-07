import { useState } from "react";
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import RestaurantHeader from "./RestaurantHeader.jsx";
import BookingChatbot from "./BookingChatbot.jsx";


const RestaurantLayout = ({ children, restaurant = { name: "PSCD Japanese Dining" } }) => {
  const [showChatbot, setShowChatbot] = useState(false);
  const openChat = () => setShowChatbot(true);
  const closeChat = () => setShowChatbot(false);
  const resolvedChildren =
    typeof children === "function" ? children({ openChat, closeChat }) : children;

  return (
    <div className="min-h-screen bg-[var(--washoku-cream)] text-[var(--washoku-ink)]">
      <RestaurantHeader onOpenChat={openChat} />
      <main className="pt-20">{resolvedChildren}</main>

      <button
        type="button"
        onClick={openChat}
        className="group fixed bottom-5 right-5 z-30 inline-flex items-center gap-3 rounded-full border border-[#c29a5b]/35 bg-[#15110f] px-5 py-3 text-left text-sm font-semibold text-[#f6ead8] shadow-[0_18px_50px_rgba(22,17,15,0.35)] transition hover:-translate-y-0.5 hover:border-[#d8b27a] hover:bg-[#1e1714]"
      >
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-[linear-gradient(145deg,_#8b2328,_#ba8a46)] shadow-[0_10px_24px_rgba(139,35,40,0.35)]">
          <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />
        </span>
        <span>
          <span className="block text-[11px] uppercase tracking-[0.28em] text-[#c9ab84]">
            AI Concierge
          </span>
          <span className="mt-0.5 block text-sm text-[#f7ebda]">Chat để giữ bàn</span>
        </span>
        <SparklesIcon className="h-5 w-5 text-[#d9b173] transition group-hover:rotate-12" />
      </button>

      {showChatbot && (
        <BookingChatbot onClose={closeChat} restaurant={restaurant} />
      )}
    </div>
  );
};

export default RestaurantLayout;
