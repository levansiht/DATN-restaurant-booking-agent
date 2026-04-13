import { useMemo, useState } from "react";
import {
  ArrowRightIcon,
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  ShoppingBagIcon,
} from "@heroicons/react/24/outline";


const formatCurrency = (value) =>
  new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));


const QUICK_FILTERS = [
  { key: "recommended", label: "Goi y" },
  { key: "bestSeller", label: "Best seller" },
  { key: "vegetarian", label: "Chay" },
  { key: "kidFriendly", label: "Tre em" },
  { key: "servedNow", label: "Dang phuc vu" },
];

const BUDGET_OPTIONS = [
  { value: "", label: "Tat ca gia" },
  { value: "150000", label: "Duoi 150k" },
  { value: "250000", label: "Duoi 250k" },
  { value: "400000", label: "Duoi 400k" },
];


const MenuExplorerSection = ({
  restaurantName,
  categories,
  items,
  loading,
  selectedItemIds = [],
  onAddItem,
  onOpenChat,
  onBookNow,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [budgetCeiling, setBudgetCeiling] = useState("");
  const [expandedItemId, setExpandedItemId] = useState(null);
  const [filters, setFilters] = useState({
    recommended: false,
    bestSeller: false,
    vegetarian: false,
    kidFriendly: false,
    servedNow: false,
  });

  const visibleItems = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return items.filter((item) => {
      if (activeCategory !== "all" && String(item.category) !== String(activeCategory)) {
        return false;
      }
      if (budgetCeiling && Number(item.price) > Number(budgetCeiling)) {
        return false;
      }
      if (filters.recommended && !item.is_recommended) {
        return false;
      }
      if (filters.bestSeller && !item.is_best_seller) {
        return false;
      }
      if (filters.vegetarian && !item.is_vegetarian) {
        return false;
      }
      if (filters.kidFriendly && !item.is_kid_friendly) {
        return false;
      }
      if (filters.servedNow && !item.is_currently_served) {
        return false;
      }
      if (!normalizedQuery) {
        return true;
      }
      const haystack = `${item.name} ${item.description || ""} ${(item.badges || []).join(" ")}`.toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [activeCategory, budgetCeiling, filters, items, searchQuery]);

  const selectedItems = useMemo(
    () => items.filter((item) => selectedItemIds.includes(item.id)),
    [items, selectedItemIds]
  );

  const highlightedItems = useMemo(
    () => items.filter((item) => item.is_best_seller || item.is_recommended).slice(0, 3),
    [items]
  );

  return (
    <section id="menu" className="px-6 py-16 md:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
              Menu that tu DB
            </div>
            <h2 className="jp-display mt-4 text-4xl font-semibold text-stone-900 md:text-5xl">
              Khach co the xem mon, loc nhanh va nho AI tu van chot mon ngay tren mot luong.
            </h2>
            <p className="mt-5 text-base leading-8 text-stone-600">
              Menu nay doc truc tiep tu du lieu van hanh cua {restaurantName}. Anh, gia, tag va
              tinh trang phuc vu deu bam cung mot nguon de bot khong goi nham mon.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => onOpenChat?.({ prompt: "Goi y 3 mon de chot nhanh giup minh." })}
              className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
            >
              <ChatBubbleLeftRightIcon className="h-5 w-5 text-[#8b2328]" />
              Nho AI tu van
            </button>
            <button
              type="button"
              onClick={onBookNow}
              className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
            >
              Dat ban
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {highlightedItems.length ? (
          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            {highlightedItems.map((item) => (
              <article
                key={`highlight-${item.id}`}
                className="overflow-hidden rounded-[2rem] border border-[#e7d4b7] bg-[linear-gradient(180deg,_#fffaf4,_#fff4e7)] shadow-[0_18px_50px_rgba(52,37,27,0.08)]"
              >
                <div className="relative h-48 overflow-hidden bg-[#efe0cd]">
                  <img
                    src={item.image_url}
                    alt={item.image_alt_text || item.name}
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute left-4 top-4 rounded-full bg-[rgba(18,14,12,0.72)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f7ead8]">
                    {item.category_name || "Mon noi bat"}
                  </div>
                </div>
                <div className="space-y-4 px-5 py-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="jp-display text-3xl font-semibold text-stone-900">{item.name}</h3>
                      <p className="mt-2 text-sm leading-7 text-stone-600">
                        {item.short_description || item.description}
                      </p>
                    </div>
                    <div className="rounded-full bg-[#f5e5d0] px-3 py-2 text-sm font-semibold text-[#8b2328]">
                      {formatCurrency(item.price)}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(item.badges || []).slice(0, 4).map((badge) => (
                      <span
                        key={`highlight-${item.id}-${badge}`}
                        className="rounded-full border border-[#dec5a2] bg-white px-3 py-1 text-[11px] font-medium text-[#6b533f]"
                      >
                        {badge}
                      </span>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : null}

        <div className="mt-10 rounded-[2rem] border border-[#ddccb2] bg-white px-5 py-5 shadow-[0_18px_50px_rgba(55,39,27,0.06)]">
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <label className="flex items-center gap-3 rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-3">
              <MagnifyingGlassIcon className="h-5 w-5 text-[#8b6b48]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="w-full bg-transparent text-sm text-stone-900 outline-none"
                placeholder="Tim mon, vi du: bo nuong, salad, trang mieng..."
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-2">
              <select
                value={activeCategory}
                onChange={(event) => setActiveCategory(event.target.value)}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-700"
              >
                <option value="all">Tat ca danh muc</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>

              <select
                value={budgetCeiling}
                onChange={(event) => setBudgetCeiling(event.target.value)}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-700"
              >
                {BUDGET_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {QUICK_FILTERS.map((filter) => (
              <button
                key={filter.key}
                type="button"
                onClick={() =>
                  setFilters((prev) => ({
                    ...prev,
                    [filter.key]: !prev[filter.key],
                  }))
                }
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  filters[filter.key]
                    ? "bg-[#8b2328] text-white shadow-[0_8px_20px_rgba(139,35,40,0.2)]"
                    : "border border-[#d9c3a1] bg-[#fff8ee] text-[#6c5545] hover:border-[#c29a5b] hover:text-[#221815]"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {selectedItems.length ? (
          <div className="mt-6 rounded-[1.8rem] border border-[#dfc8a7] bg-[linear-gradient(135deg,_#fff7ea,_#fffdf8)] px-5 py-5 shadow-[0_18px_40px_rgba(55,39,27,0.05)]">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.28em] text-[#8b6b48]">
                  Mon dang nghieng ve
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedItems.map((item) => (
                    <span
                      key={`selected-${item.id}`}
                      className="rounded-full bg-white px-3 py-2 text-sm font-medium text-[#4d3b31] shadow-sm"
                    >
                      {item.name}
                    </span>
                  ))}
                </div>
              </div>
              <button
                type="button"
                onClick={() =>
                  onOpenChat?.({
                    prompt: `Minh da nghi den ${selectedItems.map((item) => item.name).join(", ")}. Goi y combo va mon an kem giup minh.`,
                  })
                }
                className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full bg-[#16322c] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
              >
                <ShoppingBagIcon className="h-5 w-5" />
                Nho AI len combo
              </button>
            </div>
          </div>
        ) : null}

        <div className="mt-8">
          {loading ? (
            <div className="rounded-[1.8rem] border border-dashed border-stone-300 bg-white px-6 py-16 text-center text-sm text-stone-500">
              Dang tai menu that tu he thong...
            </div>
          ) : visibleItems.length === 0 ? (
            <div className="rounded-[1.8rem] border border-dashed border-stone-300 bg-white px-6 py-16 text-center text-sm text-stone-500">
              Chua co mon phu hop bo loc hien tai. Thu doi muc gia hoac nhan nho AI tu van nhe.
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
              {visibleItems.map((item) => {
                const isExpanded = expandedItemId === item.id;
                const isSelected = selectedItemIds.includes(item.id);

                return (
                  <article
                    key={item.id}
                    className="overflow-hidden rounded-[2rem] border border-[#e5d3b7] bg-white shadow-[0_18px_50px_rgba(55,39,27,0.08)]"
                  >
                    <div className="relative h-56 overflow-hidden bg-[#efe1d0]">
                      <img
                        src={item.image_url}
                        alt={item.image_alt_text || item.name}
                        className="h-full w-full object-cover transition duration-500 hover:scale-105"
                      />
                      {item.image_badge ? (
                        <span className="absolute left-4 top-4 rounded-full bg-[rgba(18,14,12,0.72)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f7ead8]">
                          {item.image_badge}
                        </span>
                      ) : null}
                    </div>

                    <div className="space-y-4 px-5 py-5">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[11px] uppercase tracking-[0.2em] text-[#8b6b48]">
                            {item.category_name || "Menu PSCD"}
                          </p>
                          <h3 className="mt-1 text-xl font-semibold text-stone-900">{item.name}</h3>
                        </div>
                        <div className="rounded-full bg-[#f5e5d0] px-3 py-2 text-sm font-semibold text-[#8b2328]">
                          {formatCurrency(item.price)}
                        </div>
                      </div>

                      <p className="text-sm leading-7 text-stone-600">
                        {isExpanded
                          ? item.description || "Mon nay hien chua co mo ta chi tiet."
                          : item.short_description || item.description || "Mon nay hien chua co mo ta chi tiet."}
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {(item.badges || []).slice(0, 5).map((badge) => (
                          <span
                            key={`${item.id}-${badge}`}
                            className="rounded-full border border-[#e3d1b6] bg-[#fff8ef] px-3 py-1 text-[11px] font-medium text-[#6c5545]"
                          >
                            {badge}
                          </span>
                        ))}
                      </div>

                      <div className="grid gap-2 sm:grid-cols-2">
                        <button
                          type="button"
                          onClick={() => setExpandedItemId(isExpanded ? null : item.id)}
                          className="rounded-2xl border border-[#d8c29f] bg-[#fff8ee] px-4 py-3 text-sm font-semibold text-[#6c5545] transition hover:border-[#c29a5b] hover:text-[#221815]"
                        >
                          {isExpanded ? "Thu gon" : "Xem chi tiet"}
                        </button>
                        <button
                          type="button"
                          onClick={() => onAddItem?.(item.id)}
                          className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                            isSelected
                              ? "bg-[#16322c] text-white"
                              : "bg-[#f4e8d7] text-[#5f4738] hover:bg-[#ead8bf]"
                          }`}
                        >
                          {isSelected ? "Da them mon" : "Them mon"}
                        </button>
                        <button
                          type="button"
                          onClick={onBookNow}
                          className="rounded-2xl bg-[#8b2328] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#a72d33]"
                        >
                          Dat ban
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            onOpenChat?.({
                              prompt: `Tu van them cho mon ${item.name} giup minh.`,
                            })
                          }
                          className="rounded-2xl border border-[#d8c29f] bg-white px-4 py-3 text-sm font-semibold text-[#6c5545] transition hover:border-[#c29a5b] hover:text-[#221815]"
                        >
                          Nho AI tu van
                        </button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default MenuExplorerSection;
