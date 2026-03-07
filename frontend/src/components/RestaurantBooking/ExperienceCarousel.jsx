import { useEffect, useState } from "react";
import {
  ArrowRightIcon,
  ChatBubbleLeftRightIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";


const ExperienceCarousel = ({ slides, onBookNow, onOpenChat }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (slides.length <= 1) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setActiveIndex((currentIndex) => (currentIndex + 1) % slides.length);
    }, 5200);

    return () => window.clearInterval(intervalId);
  }, [slides.length]);

  const goToSlide = (index) => setActiveIndex(index);
  const goToNextSlide = () => setActiveIndex((currentIndex) => (currentIndex + 1) % slides.length);
  const goToPreviousSlide = () =>
    setActiveIndex((currentIndex) => (currentIndex - 1 + slides.length) % slides.length);

  return (
    <section className="px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl rounded-[2.6rem] border border-stone-200 bg-[linear-gradient(180deg,_rgba(255,250,242,0.95),_rgba(248,239,228,0.96))] px-8 py-10 shadow-[0_24px_90px_rgba(55,39,27,0.08)]">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            <div className="text-xs uppercase tracking-[0.32em] text-[#8b6b48]">
              Món nên thử
            </div>
            <h2 className="jp-display mt-4 text-4xl font-semibold text-stone-900">
              Gợi ý những cách thưởng thức khác nhau cho một buổi tối trọn vị
            </h2>
            <p className="mt-4 text-base leading-8 text-stone-600">
              Mỗi khung gợi ý là một cách ghé quán khác nhau: hẹn hò, tụ họp bạn bè
              hoặc chọn bàn đẹp cho một dịp đặc biệt.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={goToPreviousSlide}
              className="carousel-nav-button"
              aria-label="Slide trước"
            >
              <ChevronLeftIcon className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={goToNextSlide}
              className="carousel-nav-button"
              aria-label="Slide tiếp theo"
            >
              <ChevronRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="carousel-shell mt-8">
          <div
            className="carousel-track"
            style={{ transform: `translateX(-${activeIndex * 100}%)` }}
          >
            {slides.map((slide) => (
              <article key={slide.title} className="carousel-slide">
                <div className="grid gap-7 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
                  <div className="max-w-2xl">
                    <div className="text-xs uppercase tracking-[0.3em] text-[#a1784c]">
                      {slide.eyebrow}
                    </div>
                    <h3 className="jp-display mt-4 text-4xl font-semibold leading-tight text-stone-900 md:text-5xl">
                      {slide.title}
                    </h3>
                    <p className="mt-5 text-base leading-8 text-stone-600">
                      {slide.body}
                    </p>

                    <div className="mt-6 flex flex-wrap gap-2">
                      {slide.chips.map((chip) => (
                        <span key={chip} className="lantern-chip">
                          {chip}
                        </span>
                      ))}
                    </div>

                    <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                      <button
                        type="button"
                        onClick={onBookNow}
                        className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full bg-[#8b2328] px-5 py-3 text-sm font-semibold text-white shadow-[0_16px_40px_rgba(139,35,40,0.28)] transition hover:bg-[#a72d33]"
                      >
                        Giữ bàn theo kiểu này
                        <ArrowRightIcon className="h-5 w-5" />
                      </button>
                      <button
                        type="button"
                        onClick={onOpenChat}
                        className="cta-sheen inline-flex items-center justify-center gap-2 rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                      >
                        <ChatBubbleLeftRightIcon className="h-5 w-5 text-[#8b2328]" />
                        Nhờ tư vấn thêm
                      </button>
                    </div>
                  </div>

                  <div className="carousel-visual" data-tone={slide.tone}>
                    <div className="carousel-orb carousel-orb--one"></div>
                    <div className="carousel-orb carousel-orb--two"></div>

                    <div className="relative z-10">
                      <div className="inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#f7ead8]">
                        {slide.visualLabel}
                      </div>

                      <div className="carousel-plate mt-8">
                        <div className="carousel-plate-core"></div>
                      </div>

                      <div className="mt-8 grid gap-3 sm:grid-cols-2">
                        {slide.stats.map((stat) => (
                          <div
                            key={stat.label}
                            className="rounded-[1.3rem] border border-white/12 bg-white/[0.08] px-4 py-4 backdrop-blur-sm"
                          >
                            <div className="text-[11px] uppercase tracking-[0.24em] text-white/65">
                              {stat.label}
                            </div>
                            <div className="mt-2 text-lg font-semibold text-[#fff4e4]">
                              {stat.value}
                            </div>
                          </div>
                        ))}
                      </div>

                      <p className="mt-6 rounded-[1.5rem] border border-white/10 bg-black/10 px-4 py-4 text-sm leading-7 text-white/75">
                        {slide.note}
                      </p>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            {slides.map((slide, index) => (
              <button
                key={slide.title}
                type="button"
                onClick={() => goToSlide(index)}
                className={`carousel-dot ${index === activeIndex ? "is-active" : ""}`}
                aria-label={`Chuyển đến slide ${index + 1}`}
              />
            ))}
          </div>

          <div className="text-sm text-stone-500">
            Gợi ý {activeIndex + 1}/{slides.length}
          </div>
        </div>
      </div>
    </section>
  );
};

export default ExperienceCarousel;
