import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";
import ReactMarkdown from "react-markdown";
import ChatRecommendationCard from "./ChatRecommendationCard.jsx";


const BotMessage = ({
  message,
  index,
  selectedItemIds = [],
  onQuickReply,
  onSelectRecommendation,
  onAskSimilar,
  onAddRecommendation,
}) => {
  const assistantText = message.assistantMessage || message.content || "";

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
                    isSelected={selectedItemIds.includes(item.id)}
                    onSelectItem={onSelectRecommendation}
                    onAskSimilar={onAskSimilar}
                    onAddItem={onAddRecommendation}
                  />
                ))}
              </div>
            ) : null}

            {message.upsellItems?.length ? (
              <div className="mt-4 rounded-[1.3rem] border border-[#ead8bd] bg-[#fcf5ea] p-4">
                <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#8b6b48]">
                  Goi them de ban an tron vi
                </div>
                <div className="mt-3 space-y-3">
                  {message.upsellItems.map((item) => (
                    <ChatRecommendationCard
                      key={`upsell-${item.id}`}
                      item={item}
                      isSelected={selectedItemIds.includes(item.id)}
                      onSelectItem={onSelectRecommendation}
                      onAskSimilar={onAskSimilar}
                      onAddItem={onAddRecommendation}
                    />
                  ))}
                </div>
              </div>
            ) : null}

            {message.questionToUser ? (
              <div className="mt-4 rounded-[1.2rem] border border-[#e6d2af] bg-[#faf2e5] px-4 py-3 text-sm font-medium text-[#59493e]">
                {message.questionToUser}
              </div>
            ) : null}

            {message.quickReplies?.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {message.quickReplies.map((reply) => (
                  <button
                    key={`${message.id}-${reply}`}
                    type="button"
                    onClick={() => onQuickReply?.(reply)}
                    className="rounded-full border border-[#d9c19b] bg-white px-3 py-2 text-sm text-[#6c5545] transition hover:border-[#c29a5b] hover:bg-[#fff8ee] hover:text-[#221815]"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            ) : null}

            <p className="text-[10px] text-[#8d7866]">
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
