import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";
import ReactMarkdown from "react-markdown";
import ChatRecommendationCard from "./ChatRecommendationCard.jsx";


const BotMessage = ({
  message,
  index,
  isLast = false,
  disabled = false,
  onQuickReply,
}) => {
  const assistantText = message.assistantMessage || message.content || "";
  const quickReplies = isLast ? message.quickReplies || [] : [];
  const availableTables = isLast ? message.availableTables || [] : [];
  const bookingSummary = message.bookingSummary || null;

  return (
    <div
      className="flex justify-start animate-fadeIn"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="max-w-full rounded-[1.5rem] border border-[#dfcfb7] bg-white px-4 py-3 text-[#211814] shadow-[0_10px_30px_rgba(50,34,26,0.08)]">
        <div className="flex items-start">
          <div className="mr-3 mt-1 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[linear-gradient(145deg,_#8b2328,_#ba8a46)]">
            <ChatBubbleLeftRightIcon className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1">
            <ReactMarkdown
              children={assistantText}
              skipHtml={false}
              components={{
                p: ({ ...props }) => (
                  <p className="mb-2 text-sm leading-relaxed" {...props} />
                ),
                a: ({ ...props }) => (
                  <a
                    className="text-sm text-[#8b2328] underline transition-colors hover:text-[#5f171b]"
                    rel="noopener noreferrer"
                    target="_blank"
                    {...props}
                  />
                ),
                code: ({ inline, ...props }) =>
                  inline ? (
                    <code
                      className="rounded bg-[#241a16] px-1 py-0.5 text-sm text-[#f2d8b0]"
                      {...props}
                    />
                  ) : (
                    <pre className="my-2 overflow-x-auto rounded-lg bg-[#1c1512] p-3 text-sm text-[#f6ead8]">
                      <code {...props} />
                    </pre>
                  ),
                ul: ({ ...props }) => (
                  <ul className="mb-2 ml-6 list-disc text-sm" {...props} />
                ),
                ol: ({ ...props }) => (
                  <ol className="mb-2 ml-6 list-decimal text-sm" {...props} />
                ),
                li: ({ ...props }) => <li className="mb-1 text-sm" {...props} />,
                blockquote: ({ ...props }) => (
                  <blockquote
                    className="my-2 rounded border-l-4 border-[#c29a5b] bg-[#faf2e7] py-1 pl-4 text-sm italic text-[#6e5746]"
                    {...props}
                  />
                ),
                strong: ({ ...props }) => (
                  <strong className="text-sm font-semibold" {...props} />
                ),
                em: ({ ...props }) => <em className="text-sm italic" {...props} />,
                hr: () => <hr className="my-3 border-[#e9d9be]" />,
                h1: ({ ...props }) => (
                  <h1 className="mt-2 mb-1 text-xl font-bold text-[#1f1714]" {...props} />
                ),
                h2: ({ ...props }) => (
                  <h2 className="mt-2 mb-1 text-lg font-semibold text-[#2c2018]" {...props} />
                ),
                h3: ({ ...props }) => (
                  <h3 className="mt-2 mb-1 text-base font-semibold text-[#2c2018]" {...props} />
                ),
                table: ({ ...props }) => (
                  <table
                    className="my-2 min-w-full border-collapse rounded bg-[#faf2e7]"
                    {...props}
                  />
                ),
                th: ({ ...props }) => (
                  <th
                    className="border-b border-[#dec8a5] px-2 py-1 text-left text-[#43342a]"
                    {...props}
                  />
                ),
                td: ({ ...props }) => (
                  <td
                    className="border-b border-[#eadcc4] px-2 py-1 text-[#514136]"
                    {...props}
                  />
                ),
              }}
            />

            {message.recommendedItems?.length ? (
              <div className="mt-4 space-y-3">
                {message.recommendedItems.map((item) => (
                  <ChatRecommendationCard
                    key={item.id}
                    item={item}
                  />
                ))}
              </div>
            ) : null}

            {message.upsellItems?.length ? (
              <div className="mt-4 space-y-3">
                  {message.upsellItems.map((item) => (
                    <ChatRecommendationCard
                      key={`upsell-${item.id}`}
                      item={item}
                    />
                  ))}
              </div>
            ) : null}

            {availableTables.length ? (
              <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {availableTables.map((table) => (
                  <button
                    key={table.table_id}
                    type="button"
                    disabled={disabled}
                    onClick={() => onQuickReply?.(`Bàn ${table.table_id}`)}
                    className="flex flex-col rounded-xl border border-[#d8b98a] bg-[#fbf3e7] px-3 py-2 text-left transition hover:border-[#bd8a46] hover:bg-[#f4e6d2] disabled:opacity-50"
                  >
                    <span className="text-sm font-semibold text-[#7a3b1d]">
                      Bàn {table.table_id}
                    </span>
                    <span className="text-xs text-[#6e5746]">
                      {table.table_type} · Tầng {table.floor} · {table.capacity} chỗ
                    </span>
                  </button>
                ))}
              </div>
            ) : null}

            {bookingSummary ? (
              <div className="mt-4 rounded-xl border border-[#cdb38a] bg-[#faf2e7] px-4 py-3 text-sm text-[#43342a]">
                <p className="mb-1 font-semibold text-[#7a3b1d]">Thông tin đặt bàn</p>
                <ul className="space-y-0.5">
                  {bookingSummary.table_id ? (
                    <li>
                      Bàn {bookingSummary.table_id}
                      {bookingSummary.table_type ? ` · ${bookingSummary.table_type}` : ""}
                      {bookingSummary.floor ? ` · Tầng ${bookingSummary.floor}` : ""}
                    </li>
                  ) : null}
                  {bookingSummary.booking_date ? (
                    <li>
                      {bookingSummary.booking_date}
                      {bookingSummary.booking_time ? ` lúc ${bookingSummary.booking_time}` : ""}
                    </li>
                  ) : null}
                  {bookingSummary.party_size ? <li>{bookingSummary.party_size} khách</li> : null}
                  {bookingSummary.guest_name ? <li>Tên: {bookingSummary.guest_name}</li> : null}
                  {bookingSummary.guest_phone ? <li>SĐT: {bookingSummary.guest_phone}</li> : null}
                  {bookingSummary.guest_email ? <li>Email: {bookingSummary.guest_email}</li> : null}
                </ul>
                {message.bookingCode ? (
                  <p className="mt-2 font-semibold text-[#7a3b1d]">
                    Mã đặt bàn: {message.bookingCode}
                  </p>
                ) : null}
              </div>
            ) : null}

            {quickReplies.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {quickReplies.map((reply) => (
                  <button
                    key={reply}
                    type="button"
                    disabled={disabled}
                    onClick={() => onQuickReply?.(reply)}
                    className="rounded-full border border-[#d8b98a] bg-[#fbf3e7] px-3 py-1.5 text-xs font-medium text-[#7a3b1d] transition hover:border-[#bd8a46] hover:bg-[#f4e6d2] disabled:opacity-50"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            ) : null}

            <p className="mt-2 text-[10px] text-[#8d7866]">
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BotMessage;
