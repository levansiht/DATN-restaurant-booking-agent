const formatCurrency = (value) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));


const ChatRecommendationCard = ({
  item,
  isSelected = false,
  onSelectItem,
  onAskSimilar,
  onAddItem,
}) => {
  return (
    <article className="overflow-hidden rounded-[1.4rem] border border-[#e7d7bf] bg-[#fffaf3] shadow-[0_12px_28px_rgba(55,39,27,0.08)]">
      <div className="relative h-40 overflow-hidden bg-[#efe5d6]">
        <img
          src={item.image_url}
          alt={item.image_alt_text || item.name}
          className="h-full w-full object-cover"
        />
        {item.image_badge ? (
          <span className="absolute left-3 top-3 rounded-full bg-[rgba(18,14,12,0.72)] px-2.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-[#f7ead8]">
            {item.image_badge}
          </span>
        ) : null}
      </div>

      <div className="space-y-4 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#8b6b48]">
              {item.category_name || "Menu PSCD"}
            </p>
            <h4 className="mt-1 text-base font-semibold text-[#1f1714]">{item.name}</h4>
          </div>
          <div className="rounded-full bg-[#f4e7d2] px-3 py-1 text-sm font-semibold text-[#8b2328]">
            {formatCurrency(item.price)}
          </div>
        </div>

        <p className="text-sm leading-6 text-[#5e4b3f]">{item.short_reason}</p>

        {item.tags?.length ? (
          <div className="flex flex-wrap gap-1.5">
            {item.tags.slice(0, 4).map((tag) => (
              <span
                key={`${item.id}-${tag}`}
                className="rounded-full border border-[#e6d6bc] bg-white px-2.5 py-0.5 text-[10px] font-medium leading-5 text-[#735846]"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        <div className="grid gap-2 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => onSelectItem?.(item)}
            className="rounded-2xl bg-[#8b2328] px-3 py-2 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
          >
            {isSelected ? "Đã chọn" : "Chọn món này"}
          </button>
          <button
            type="button"
            onClick={() => onAskSimilar?.(item)}
            className="rounded-2xl border border-[#d7c1a0] bg-white px-3 py-2 text-sm font-semibold text-[#6d5442] transition hover:border-[#c29a5b] hover:text-[#2a201a]"
          >
            Xem món tương tự
          </button>
          <button
            type="button"
            onClick={() => onAddItem?.(item)}
            className="rounded-2xl border border-[#d7c1a0] bg-[#f9f1e6] px-3 py-2 text-sm font-semibold text-[#6d5442] transition hover:border-[#c29a5b] hover:bg-white"
          >
            {isSelected ? "Đã thêm" : "Thêm vào đơn"}
          </button>
        </div>
      </div>
    </article>
  );
};

export default ChatRecommendationCard;
