import { useEffect, useEffectEvent, useRef, useState } from "react";
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  SparklesIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import { useStreamingResponseV2 } from "../../hooks/useStreamingResponseV2";
import BotMessage from "./BotMessage";
import Thinking from "./Thinking";
import UserMessage from "./UserMessage";


const QUICK_ACTIONS = [
  "Goi y 3 mon de an cho 2 nguoi",
  "Menu dang co mon nao noi bat?",
  "Tu van combo nhe cho nhom nho",
  "Toi nay con ban cho 2 nguoi khong?",
];


const BookingChatbot = ({
  onClose,
  restaurant,
  selectedItemIds = [],
  onAddMenuItem,
  chatSeed,
}) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const messagesEndRef = useRef(null);
  const lastSeedIdRef = useRef(0);
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

  const buildBotFallback = () => ({
    assistantMessage:
      "Xin loi, PSCD dang gap su co khi phan hoi. Anh/chi vui long thu lai sau it phut.",
    content:
      "Xin loi, PSCD dang gap su co khi phan hoi. Anh/chi vui long thu lai sau it phut.",
    recommendedItems: [],
    upsellItems: [],
    quickReplies: [],
    questionToUser: "",
  });

  const sendMessage = async (rawText) => {
    const userInput = rawText?.trim();
    if (!userInput) {
      return;
    }

    if (!hasStartedChat) {
      setHasStartedChat(true);
    }

    const baseTimestamp = Date.now();
    const userMessage = {
      id: baseTimestamp,
      type: "user",
      content: userInput,
      timestamp: new Date(),
    };

    const botMessageId = baseTimestamp + 1;
    const botMessage = {
      id: botMessageId,
      type: "bot",
      content: "",
      assistantMessage: "",
      recommendedItems: [],
      upsellItems: [],
      quickReplies: [],
      questionToUser: "",
      timestamp: new Date(),
    };

    setMessages((previousMessages) => [...previousMessages, userMessage, botMessage]);
    setInputMessage("");

    try {
      const chatHistory = messages.map((message) => ({
        role: message.type === "user" ? "user" : "assistant",
        content: message.assistantMessage || message.content || "",
      }));

      await streamResponse({
        user_input: userInput,
        chat_history: chatHistory,
        selected_item_ids: selectedItemIds,
        onPayload: (payload) => {
          updateBotMessage(botMessageId, {
            content: payload?.assistant_message || "",
            assistantMessage: payload?.assistant_message || "",
            recommendedItems: payload?.recommended_items || [],
            upsellItems: payload?.upsell_items || [],
            quickReplies: payload?.quick_replies || [],
            questionToUser: payload?.question_to_user || "",
            intent: payload?.intent || "",
            nextAction: payload?.next_action || "none",
          });
        },
        onFinish: ({ payload, content }) => {
          if (payload) {
            updateBotMessage(botMessageId, {
              content: payload?.assistant_message || content || "",
              assistantMessage: payload?.assistant_message || content || "",
              recommendedItems: payload?.recommended_items || [],
              upsellItems: payload?.upsell_items || [],
              quickReplies: payload?.quick_replies || [],
              questionToUser: payload?.question_to_user || "",
              intent: payload?.intent || "",
              nextAction: payload?.next_action || "none",
            });
            return;
          }

          if (content) {
            updateBotMessage(botMessageId, {
              content,
              assistantMessage: content,
            });
            return;
          }

          updateBotMessage(botMessageId, buildBotFallback());
        },
        onError: () => {
          updateBotMessage(botMessageId, buildBotFallback());
        },
      });
    } catch (error) {
      console.error("Error sending message:", error);
      updateBotMessage(botMessageId, buildBotFallback());
    }
  };

  const replaySeedPrompt = useEffectEvent((prompt) => {
    void sendMessage(prompt);
  });

  useEffect(() => {
    if (!chatSeed?.id || !chatSeed?.prompt || lastSeedIdRef.current === chatSeed.id) {
      return;
    }
    lastSeedIdRef.current = chatSeed.id;
    replaySeedPrompt(chatSeed.prompt);
  }, [chatSeed, replaySeedPrompt]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await sendMessage(inputMessage);
  };

  const handleQuickAction = async (action) => {
    await sendMessage(action);
  };

  const handleSelectRecommendation = async (item) => {
    onAddMenuItem?.(item.id);
    await sendMessage(`Minh nghiêng ve mon ${item.name}. Goi y them mon an kem nhe.`);
  };

  const handleAskSimilar = async (item) => {
    await sendMessage(`Goi y mon tuong tu mon ${item.name} giup minh.`);
  };

  const handleAddRecommendation = (item) => {
    onAddMenuItem?.(item.id);
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-end justify-end bg-[rgba(18,14,12,0.38)] px-4 pb-4 pt-24 ${
        isClosing ? "animate-fadeOut" : "animate-fadeIn"
      }`}
    >
      <div
        className={`flex h-[min(86vh,860px)] w-full max-w-2xl flex-col overflow-hidden rounded-[2rem] border border-[#c29a5b]/25 bg-[#f7f0e5] shadow-[0_40px_120px_rgba(24,16,14,0.35)] transition-all duration-500 ease-in-out ${
          isClosing ? "animate-slideDown" : "animate-slideUp"
        }`}
      >
        <div className="flex items-center justify-between border-b border-[#d8c4a3] bg-[linear-gradient(135deg,_#171211,_#3a1715)] px-5 py-4 text-white">
          <div className="flex items-center">
            <div className="mr-3 flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-[linear-gradient(145deg,_#8b2328,_#b78946)]">
              <ChatBubbleLeftRightIcon className="h-5 w-5" />
            </div>
            <div>
              <span className="jp-display text-2xl font-semibold">PSCD Tu van mon & ban</span>
              <p className="text-xs uppercase tracking-[0.28em] text-[#d6be9b]">
                Sales assistant
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

        {selectedItemIds.length ? (
          <div className="border-b border-[#dfd0b8] bg-[#fff8ee] px-5 py-3">
            <div className="flex items-center gap-2 text-sm font-medium text-[#5f4738]">
              <SparklesIcon className="h-4 w-4 text-[#8b2328]" />
              Dang co {selectedItemIds.length} mon duoc quan tam. Bot se uu tien goi y combo va mon an kem sat hon.
            </div>
          </div>
        ) : null}

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
                  Tu van ban hang
                </p>
                <h3 className="jp-display mt-3 text-3xl font-semibold text-[#1f1815]">
                  PSCD se giup minh chon mon de nhin, de chot va de dat ban dung luc.
                </h3>
                <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-[#645245]">
                  Hoi menu, ngan sach, combo nhe cho 2 nguoi, mon cho tre em hoac nho bot
                  goi y mon roi chuyen sang dat ban nhanh tai {restaurant.name}.
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

                if (index === messages.length - 1 && thinking && !message.assistantMessage) {
                  return <Thinking key={message.id} />;
                }

                return (
                  <BotMessage
                    key={message.id}
                    index={index}
                    message={message}
                    selectedItemIds={selectedItemIds}
                    onQuickReply={handleQuickAction}
                    onSelectRecommendation={handleSelectRecommendation}
                    onAskSimilar={handleAskSimilar}
                    onAddRecommendation={handleAddRecommendation}
                  />
                );
              })}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {!hasStartedChat ? (
          <div className="border-t border-[#dfd0b8] bg-[#f9f2e7] px-6 py-4">
            <p className="mb-3 text-sm font-semibold text-[#43342a]">
              Lua chon nhanh:
            </p>
            <div className="flex flex-wrap gap-2">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => handleQuickAction(action)}
                  className="rounded-full border border-[#d4ba93] bg-white px-4 py-2 text-sm text-[#6c5545] transition hover:border-[#c29a5b] hover:bg-[#fff7eb] hover:text-[#221815]"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <form
          onSubmit={handleSubmit}
          className="border-t border-[#dcc9a7] bg-white px-5 py-4"
        >
          <div className="flex items-end gap-3">
            <textarea
              value={inputMessage}
              onChange={(event) => setInputMessage(event.target.value)}
              placeholder="Vi du: Di 2 nguoi, minh muon set de an va neu hop thi dat ban luc 19:30"
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
                  : "cursor-not-allowed bg-stone-300"
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
