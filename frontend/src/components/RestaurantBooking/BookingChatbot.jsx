import { useEffect, useRef, useState } from "react";
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useStreamingResponseV2 } from "../../hooks/useStreamingResponseV2";
import BotMessage from "./BotMessage";
import Thinking from "./Thinking";
import UserMessage from "./UserMessage";


const QUICK_ACTIONS = [
  "Tối nay còn bàn cho 2 người không?",
  "Tôi muốn bàn gần cửa sổ lúc 19:30",
  "Tư vấn bàn cho nhóm 6 người",
  "Ngày mai tầng 1 còn bàn nào đẹp không?",
];


const BookingChatbot = ({ onClose, restaurant }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const messagesEndRef = useRef(null);
  const { streamResponse, thinking } = useStreamingResponseV2();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 300);
  };

  const updateBotMessage = (id, data) => {
    setMessages((previousMessages) =>
      previousMessages.map((message) =>
        message.id === id ? { ...message, ...data } : message
      )
    );
  };

  const handleSendMessage = async (event, text = null) => {
    event.preventDefault();
    const userInput = text || inputMessage;

    if (!userInput.trim()) {
      return;
    }

    if (!hasStartedChat) {
      setHasStartedChat(true);
    }

    const userMessage = {
      id: Date.now(),
      type: "user",
      content: userInput,
      timestamp: new Date(),
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setInputMessage("");

    const botMessageId = Date.now() + 1;
    const botMessage = {
      id: botMessageId,
      type: "bot",
      content: "",
      timestamp: new Date(),
    };

    setMessages((previousMessages) => [...previousMessages, botMessage]);

    try {
      const chatHistory = messages.map((message) => ({
        role: message.type === "user" ? "user" : "assistant",
        content: message.content,
      }));

      await streamResponse({
        user_input: userInput,
        chat_history: chatHistory,
        onProgress: ({ type, content }) => {
          if (type === "token") {
            updateBotMessage(botMessageId, { content });
          }
        },
        onFinish: ({ content }) => {
          updateBotMessage(botMessageId, { content });
        },
        onError: () => {
          updateBotMessage(botMessageId, {
            content: "Xin lỗi, PSCD đang gặp sự cố khi phản hồi. Anh/chị vui lòng thử lại sau ít phút.",
          });
        },
      });
    } catch (error) {
      console.error("Error sending message:", error);
      updateBotMessage(botMessageId, {
        content: "Xin lỗi, PSCD đang gặp sự cố khi phản hồi. Anh/chị vui lòng thử lại sau ít phút.",
      });
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-end justify-end bg-[rgba(18,14,12,0.38)] px-4 pb-4 pt-24 ${
        isClosing ? "animate-fadeOut" : "animate-fadeIn"
      }`}
    >
      <div
        className={`flex h-[min(82vh,780px)] w-full max-w-xl flex-col overflow-hidden rounded-[2rem] border border-[#c29a5b]/25 bg-[#f7f0e5] shadow-[0_40px_120px_rgba(24,16,14,0.35)] transition-all duration-500 ease-in-out ${
          isClosing ? "animate-slideDown" : "animate-slideUp"
        }`}
      >
        <div className="flex items-center justify-between border-b border-[#d8c4a3] bg-[linear-gradient(135deg,_#171211,_#3a1715)] px-5 py-4 text-white">
          <div className="flex items-center">
            <div className="mr-3 flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-[linear-gradient(145deg,_#8b2328,_#b78946)]">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
            </div>
            <div>
              <span className="jp-display text-2xl font-semibold">PSCD Tư vấn bàn</span>
              <p className="text-xs uppercase tracking-[0.28em] text-[#d6be9b]">
                Hỗ trợ giữ chỗ
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-xl p-2 text-white/80 transition hover:bg-white/10 hover:text-white"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div
          className={`flex-1 space-y-4 overflow-x-hidden bg-[radial-gradient(circle_at_top_left,_rgba(194,154,91,0.16),_transparent_30%),linear-gradient(180deg,_#f9f4eb_0%,_#f4eadc_100%)] p-6 ${
            hasStartedChat ? "overflow-y-auto" : "overflow-hidden"
          }`}
        >
          {!hasStartedChat ? (
            <div className="flex h-full items-center justify-center overflow-hidden">
              <div className="w-full px-4 text-center">
                <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-[linear-gradient(145deg,_#8b2328,_#ba8a46)] shadow-[0_18px_40px_rgba(139,35,40,0.28)]">
                  <ChatBubbleLeftRightIcon className="h-8 w-8 text-white" />
                </div>
                <p className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
                  Gợi ý giữ bàn nhanh
                </p>
                <h3 className="jp-display mt-3 text-3xl font-semibold text-[#1f1815]">
                  PSCD sẽ cùng bạn chọn đúng bàn, đúng giờ và đúng không gian.
                </h3>
                <p className="mx-auto mt-4 max-w-md text-sm leading-7 text-[#645245]">
                  Hãy hỏi về bàn trống, vị trí tầng, số lượng khách hoặc nhờ chatbot hỗ
                  trợ gom đủ thông tin để đặt bàn nhanh tại {restaurant.name}.
                </p>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message, index) => {
                if (message.type === "user") {
                  return (
                    <UserMessage
                      key={message.id}
                      index={index}
                      message={message}
                    />
                  );
                }

                if (index === messages.length - 1 && thinking) {
                  return <Thinking key={message.id} />;
                }

                return (
                  <BotMessage
                    key={message.id}
                    index={index}
                    message={message}
                  />
                );
              })}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-[#dfd0b8] bg-[#f9f2e7] px-6 py-4">
          <p className="mb-3 text-sm font-semibold text-[#43342a]">
            Lựa chọn nhanh:
          </p>
          <div className="flex flex-wrap gap-2">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action}
                type="button"
                onClick={(event) => handleSendMessage(event, action)}
                className="rounded-full border border-[#d4ba93] bg-white px-4 py-2 text-sm text-[#6c5545] transition hover:border-[#c29a5b] hover:bg-[#fff7eb] hover:text-[#221815]"
              >
                {action}
              </button>
            ))}
          </div>
        </div>

        <form
          onSubmit={handleSendMessage}
          className="border-t border-[#dcc9a7] bg-white px-5 py-4"
        >
          <div className="flex items-end gap-3">
            <textarea
              value={inputMessage}
              onChange={(event) => setInputMessage(event.target.value)}
              placeholder="Ví dụ: Tôi muốn bàn cho 4 người lúc 19:30 tối nay"
              className="min-h-[52px] flex-1 resize-none rounded-2xl border border-[#dbc7a7] bg-[#fbf6ef] px-4 py-3 text-sm text-[#211814] outline-none transition focus:border-[#c29a5b] focus:bg-white"
              rows={1}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  if (inputMessage.trim()) {
                    event.currentTarget.form?.requestSubmit();
                  }
                }
              }}
            />
            <button
              type="submit"
              disabled={!inputMessage.trim()}
              className={`flex h-12 w-12 items-center justify-center rounded-2xl text-white transition ${
                inputMessage.trim()
                  ? "bg-[#8b2328] hover:bg-[#a72d33]"
                  : "bg-stone-300 cursor-not-allowed"
              }`}
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BookingChatbot;
