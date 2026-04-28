import { useEffect, useRef, useState } from "react";
import { PaperAirplaneIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { useStreamingResponseV2 } from "../../hooks/useStreamingResponseV2";
import BotMessage from "./BotMessage";
import Thinking from "./Thinking";
import UserMessage from "./UserMessage";


const BookingChatbot = ({
  onClose,
  restaurant,
  selectedItemIds = [],
  chatSeed,
}) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const messagesEndRef = useRef(null);
  const lastSeedIdRef = useRef(0);
  const sendMessageRef = useRef(null);
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
      "Xin lỗi, PSCD đang gặp sự cố khi phản hồi. Mình vui lòng thử lại sau ít phút.",
    content:
      "Xin lỗi, PSCD đang gặp sự cố khi phản hồi. Mình vui lòng thử lại sau ít phút.",
    recommendedItems: [],
    upsellItems: [],
    quickReplies: [],
    questionToUser: "",
    nextQuestion: "",
    softClose: "",
    conversationGoal: "",
    saleStage: "",
    bookingFieldsNeeded: [],
  });

  const mapPayloadToBotState = (payload, fallbackContent = "") => ({
    content: payload?.assistant_message || fallbackContent || "",
    assistantMessage: payload?.assistant_message || fallbackContent || "",
    recommendedItems: payload?.recommended_items || [],
    upsellItems: payload?.upsell_items || [],
    quickReplies: payload?.quick_replies || [],
    questionToUser: payload?.question_to_user || payload?.next_question || "",
    nextQuestion: payload?.next_question || "",
    softClose: payload?.soft_close || "",
    conversationGoal: payload?.conversation_goal || "",
    saleStage: payload?.sale_stage || "",
    bookingFieldsNeeded: payload?.booking_fields_needed || [],
    intent: payload?.intent || "",
    nextAction: payload?.next_action || "none",
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
      nextQuestion: "",
      softClose: "",
      conversationGoal: "",
      saleStage: "",
      bookingFieldsNeeded: [],
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
          updateBotMessage(botMessageId, mapPayloadToBotState(payload));
        },
        onFinish: ({ payload, content }) => {
          if (payload) {
            updateBotMessage(botMessageId, mapPayloadToBotState(payload, content));
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

  sendMessageRef.current = sendMessage;

  useEffect(() => {
    if (!chatSeed?.id || !chatSeed?.prompt || lastSeedIdRef.current === chatSeed.id) {
      return;
    }
    lastSeedIdRef.current = chatSeed.id;
    void sendMessageRef.current?.(chatSeed.prompt);
  }, [chatSeed]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await sendMessage(inputMessage);
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
            <div>
              <span className="jp-display text-2xl font-semibold">{restaurant.name}</span>
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
            <div className="h-full" />
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
                  />
                );
              })}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form
          onSubmit={handleSubmit}
          className="border-t border-[#dcc9a7] bg-white px-5 py-4"
        >
          <div className="flex items-end gap-3">
            <textarea
              value={inputMessage}
              onChange={(event) => setInputMessage(event.target.value)}
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
