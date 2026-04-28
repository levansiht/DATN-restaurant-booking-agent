const formatCurrency = (value) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));


const ChatRecommendationCard = ({ item }) => {
  return (
    <article className="rounded-xl border border-[#e7d7bf] bg-[#fffaf3] px-4 py-3">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          {item.category_name ? (
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#8b6b48]">
              {item.category_name}
            </p>
          ) : null}
          <h4 className="mt-1 text-sm font-semibold text-[#1f1714]">{item.name}</h4>
        </div>
        <div className="shrink-0 text-sm font-semibold text-[#8b2328]">
          {formatCurrency(item.price)}
        </div>
      </div>
    </article>
  );
};

export default ChatRecommendationCard;
