"use client";

import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { ChatWidget } from "@/components/ChatWidget";
import { createPublicCallback, BookingApiError } from "@/lib/public-booking";
import { translations } from "@/lib/landing-i18n";
import type { Lang, Translations } from "@/lib/landing-i18n";

// ─────────────────────────────────────────────────────────
// Hooks
// ─────────────────────────────────────────────────────────

function useInView(threshold = 0.13) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || visible) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold });
    obs.observe(el);
    return () => obs.disconnect();
  }, [visible, threshold]);
  return { ref, visible };
}

function useCountUp(target: number, duration = 1700, active = false) {
  const [count, setCount] = useState(0);
  const [popped, setPopped] = useState(false);
  useEffect(() => {
    if (!active) return;
    const t0 = performance.now();
    let raf: number;
    const tick = (now: number) => {
      const p = Math.min((now - t0) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setCount(Math.round(ease * target));
      if (p < 1) raf = requestAnimationFrame(tick);
      else { setCount(target); setPopped(true); setTimeout(() => setPopped(false), 400); }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, target, duration]);
  return { count, popped };
}

// ─────────────────────────────────────────────────────────
// Animated section wrapper — spring physics feel
// ─────────────────────────────────────────────────────────

type AnimFrom = "bottom" | "left" | "right" | "scale" | "fade";
const ORIGIN: Record<AnimFrom, string> = {
  bottom: "translateY(30px)",
  left:   "translateX(-28px)",
  right:  "translateX(28px)",
  scale:  "scale(0.93)",
  fade:   "none",
};

function Anim({
  children, delay = 0, className = "", from = "bottom",
}: {
  children: React.ReactNode; delay?: number; className?: string; from?: AnimFrom;
}) {
  const { ref, visible } = useInView();
  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "none" : ORIGIN[from],
        transition: `opacity 0.65s cubic-bezier(0.22,1,0.36,1) ${delay}ms,
                     transform 0.65s cubic-bezier(0.22,1,0.36,1) ${delay}ms`,
        willChange: "opacity, transform",
      }}
    >
      {children}
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// Language context
// ─────────────────────────────────────────────────────────

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: Translations };
const LangCtx = createContext<Ctx>({} as Ctx);
const useT = () => useContext(LangCtx);

// ─────────────────────────────────────────────────────────
// Scroll progress bar
// ─────────────────────────────────────────────────────────

function ScrollProgress() {
  useEffect(() => {
    const el = document.getElementById("scroll-progress");
    if (!el) return;
    const update = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      el.style.width = h > 0 ? `${(window.scrollY / h) * 100}%` : "0%";
    };
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);
  return <div id="scroll-progress" />;
}

// ─────────────────────────────────────────────────────────
// Waveform
// ─────────────────────────────────────────────────────────

const WAVE_HEIGHTS = [0.3, 0.65, 0.45, 0.9, 0.55, 0.8, 0.35, 1.0, 0.6, 0.4,
                      0.85, 0.5, 0.95, 0.7, 0.4, 0.9, 0.55, 0.75, 0.3, 0.65,
                      0.45, 0.85, 0.4, 0.7, 0.5, 0.9, 0.35, 0.6];

function Waveform() {
  return (
    <div className="flex items-center justify-center gap-[3px] h-10">
      {WAVE_HEIGHTS.map((h, i) => (
        <div
          key={i}
          className="wave-bar w-[3px] rounded-full bg-teal-300"
          style={{
            height: `${Math.round(h * 32) + 4}px`,
            animationDelay: `${i * 42}ms`,
            opacity: 0.55 + h * 0.45,
          }}
        />
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// HEADER
// ─────────────────────────────────────────────────────────

function Header() {
  const { lang, setLang, t } = useT();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("home");

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const sections = ["home", "services", "ai", "doctors", "faq", "contact"];
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) setActiveSection(e.target.id); });
      },
      { rootMargin: "-40% 0px -55% 0px" }
    );
    sections.forEach((id) => { const el = document.getElementById(id); if (el) obs.observe(el); });
    return () => obs.disconnect();
  }, []);

  const links = [
    { href: "#services", id: "services", label: t.nav.services },
    { href: "#doctors",  id: "doctors",  label: t.nav.doctors  },
    { href: "#ai",       id: "ai",       label: t.nav.ai       },
    { href: "#faq",      id: "faq",      label: t.nav.faq      },
    { href: "#contact",  id: "contact",  label: t.nav.contact  },
  ];

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-white/98 shadow-[0_1px_0_0_rgba(0,0,0,0.06)]" : "bg-white/95"
      }`}
      style={{ backdropFilter: scrolled ? "blur(12px)" : "none" }}
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <a href="#home" className="flex shrink-0 items-center gap-2 group">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-500 transition-transform duration-200 group-hover:scale-105">
              <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.5} className="h-4 w-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12M6 12h12" />
              </svg>
            </div>
            <span className="text-[15px] font-bold text-gray-900">
              UroClinic <span className="text-teal-500">AI</span>
            </span>
          </a>

          {/* Desktop nav */}
          <nav className="hidden items-center gap-0.5 lg:flex">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className={`relative rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  activeSection === l.id
                    ? "text-teal-600"
                    : "text-gray-500 hover:text-gray-900"
                }`}
              >
                {l.label}
                {activeSection === l.id && (
                  <span className="absolute bottom-1 left-3 right-3 h-0.5 rounded-full bg-teal-500" />
                )}
              </a>
            ))}
          </nav>

          {/* Right controls */}
          <div className="flex shrink-0 items-center gap-2.5">
            {/* Lang switcher */}
            <div className="flex overflow-hidden rounded-full border border-gray-200 text-[11px] font-bold">
              {(["uz", "ru"] as Lang[]).map((l, i) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`px-3 py-1.5 transition-all ${
                    lang === l
                      ? "bg-teal-500 text-white"
                      : "text-gray-400 hover:bg-gray-50"
                  } ${i === 1 ? "border-l border-gray-200" : ""}`}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>

            <a
              href="/yozilish"
              className="hidden rounded-full bg-teal-500 px-5 py-2 text-sm font-semibold text-white transition-all hover:bg-teal-600 hover:shadow-md hover:shadow-teal-200 active:scale-95 sm:inline-flex"
            >
              {t.nav.book}
            </a>

            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 lg:hidden"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
                {menuOpen
                  ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  : <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="border-t border-gray-100 pb-4 pt-2 lg:hidden">
            {links.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-3 py-2.5 text-sm font-medium text-gray-600 hover:bg-teal-50 hover:text-teal-600"
              >
                {l.label}
              </a>
            ))}
            <a
              href="/yozilish"
              onClick={() => setMenuOpen(false)}
              className="mt-2 block rounded-full bg-teal-500 px-4 py-2.5 text-center text-sm font-semibold text-white"
            >
              {t.nav.book}
            </a>
          </div>
        )}
      </div>
    </header>
  );
}

// ─────────────────────────────────────────────────────────
// HERO
// ─────────────────────────────────────────────────────────

function Hero() {
  const { t, lang } = useT();
  const { ref, visible } = useInView(0.05);
  const { count: calls,    popped: callPopped    } = useCountUp(42, 1800, visible);
  const { count: bookings, popped: bookingPopped } = useCountUp(18, 2000, visible);

  const fadeLeft = {
    opacity:    visible ? 1 : 0,
    transform:  visible ? "none" : "translateX(-20px)",
    transition: "opacity 0.7s cubic-bezier(0.22,1,0.36,1), transform 0.7s cubic-bezier(0.22,1,0.36,1)",
  };
  const fadeRight = {
    opacity:    visible ? 1 : 0,
    transform:  visible ? "none" : "translateX(20px)",
    transition: "opacity 0.7s cubic-bezier(0.22,1,0.36,1) 0.18s, transform 0.7s cubic-bezier(0.22,1,0.36,1) 0.18s",
  };

  const badges = lang === "uz"
    ? ["UZ/RU", "24/7 AI yordamchi", "Operatorga ulash"]
    : ["UZ/RU", "24/7 AI ассистент", "Переключение на оператора"];

  return (
    <section id="home" ref={ref} className="bg-white pt-24 pb-16 sm:pt-28 sm:pb-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">

          {/* Left column */}
          <div style={fadeLeft}>
            <p className="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-teal-500">
              {lang === "uz" ? "UROLOGIYA KLINIKASI" : "УРОЛОГИЧЕСКАЯ КЛИНИКА"}
            </p>
            <h1 className="text-[2.6rem] font-extrabold leading-[1.08] tracking-tight text-gray-900 sm:text-5xl">
              {t.hero.title}
              <br />
              <span className="text-gray-900">{t.hero.highlight}</span>
            </h1>
            <p className="mt-5 max-w-md text-[15px] leading-relaxed text-gray-500">
              {t.hero.desc}
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <a
                href="tel:+998712345678"
                className="inline-flex items-center gap-2 rounded-full border border-gray-200 px-5 py-2.5 text-sm font-semibold text-gray-700 transition-all hover:border-teal-300 hover:text-teal-600 active:scale-95"
              >
                {t.hero.btnCall}
              </a>
              <a
                href="/yozilish"
                className="inline-flex items-center gap-2 rounded-full bg-teal-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-teal-600 hover:shadow-md hover:shadow-teal-200 active:scale-95"
              >
                {t.hero.btnBook}
              </a>
            </div>

            {/* Badges */}
            <div className="mt-5 flex flex-wrap gap-2">
              {badges.map((b, i) => (
                <span
                  key={b}
                  className="badge-in rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500"
                  style={{ animationDelay: `${0.4 + i * 0.1}s` }}
                >
                  {b}
                </span>
              ))}
            </div>
          </div>

          {/* Right column: AI stats card */}
          <div style={fadeRight}>
            <div className="overflow-hidden rounded-2xl bg-white shadow-[0_4px_32px_rgba(0,0,0,0.1)] ring-1 ring-gray-100">

              {/* Header row */}
              <div className="flex items-start gap-3 p-5 pb-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-500">
                  <span className="text-xs font-bold text-white">AI</span>
                </div>
                <div>
                  <p className="font-semibold text-gray-900">
                    {lang === "uz" ? "AI telefon yordamchi faol" : "AI телефонный ассистент активен"}
                  </p>
                  <p className="mt-0.5 text-[13px] leading-snug text-gray-500">
                    {lang === "uz"
                      ? "Qo'ng'iroqlarni qabul qiladi, yozuvga yordam beradi va operatorga ulaydi."
                      : "Принимает звонки, помогает с записью и переключает на оператора."}
                  </p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 border-t border-gray-100">
                <div className="border-r border-gray-100 px-5 py-4">
                  <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">
                    {lang === "uz" ? "Bugungi qo'ng'iroqlar" : "Звонков сегодня"}
                  </p>
                  <p className={`mt-1.5 text-4xl font-extrabold text-gray-900 tabular-nums ${callPopped ? "count-pop" : ""}`}>
                    {calls}
                  </p>
                </div>
                <div className="px-5 py-4">
                  <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">
                    {lang === "uz" ? "Qabul so'rovlari" : "Записей"}
                  </p>
                  <p className={`mt-1.5 text-4xl font-extrabold text-gray-900 tabular-nums ${bookingPopped ? "count-pop" : ""}`}>
                    {bookings}
                  </p>
                </div>
              </div>

              {/* Waveform panel */}
              <div className="mx-4 my-3 overflow-hidden rounded-xl bg-[#0B2D3A] px-4 py-3.5">
                <Waveform />
              </div>

              {/* Safety note */}
              <div className="px-5 pb-4">
                <p className="text-[12px] leading-relaxed text-teal-600">
                  {lang === "uz"
                    ? "AI diagnoz qo'ymaydi. Tibbiy savollar operator yoki shifokorga yo'naltiriladi."
                    : "AI не ставит диагнозы. Медицинские вопросы направляются к врачу или оператору."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// TRUST
// ─────────────────────────────────────────────────────────

function Trust() {
  const { t } = useT();
  return (
    <section className="bg-[#F8FAFC] py-12 sm:py-14">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {t.trust.items.slice(0, 4).map((item, i) => (
            <Anim key={i} delay={i * 65} from="bottom">
              <div className="group rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100/80 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:ring-teal-100">
                <p className="font-semibold text-[14px] text-gray-900">{item.title}</p>
                <p className="mt-1.5 text-xs leading-relaxed text-gray-500">{item.desc}</p>
              </div>
            </Anim>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// SERVICES
// ─────────────────────────────────────────────────────────

function Services() {
  const { t, lang } = useT();
  return (
    <section id="services" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Anim className="mb-12">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-teal-500">
            {lang === "uz" ? "XIZMATLAR" : "УСЛУГИ"}
          </p>
          <h2 className="text-[2rem] font-extrabold text-gray-900">{t.services.title}</h2>
          <p className="mt-3 max-w-xl text-[15px] text-gray-500">{t.services.sub}</p>
        </Anim>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {t.services.items.map((svc, i) => (
            <Anim key={i} delay={i * 55} from="bottom">
              <div className="group flex items-start gap-4 rounded-2xl bg-white p-5 ring-1 ring-gray-100 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:ring-teal-100">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-500 text-[13px] font-bold text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
                  {i + 1}
                </div>
                <div>
                  <p className="font-semibold text-[14px] text-gray-900">{svc.title}</p>
                  <p className="mt-1.5 text-xs leading-relaxed text-gray-500">{svc.desc}</p>
                </div>
              </div>
            </Anim>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// AI SECTION
// ─────────────────────────────────────────────────────────

function AISection() {
  const { t, lang } = useT();
  const { ref, visible } = useInView(0.1);

  const flowSteps = lang === "uz"
    ? ["Tinglash", "Ma'lumotni aniqlash", "Javob berish", "Operatorga ulash"]
    : ["Прослушивание", "Уточнение запроса", "Ответ пациенту", "Переключение на оператора"];

  const flowSub = lang === "uz" ? "Xavfsiz nazoratli jarayon" : "Безопасный контролируемый процесс";

  const badgeLabels = lang === "uz"
    ? ["24/7 qo'ng'iroq", "UZ/RU muloqot", "Operatorga ulash", "Xavfsizlik"]
    : ["Звонки 24/7", "UZ/RU общение", "Переключение", "Безопасность"];

  return (
    <section id="ai" className="py-20 sm:py-24" style={{ backgroundColor: "#0B2D3A" }}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">

          {/* Left */}
          <Anim from="left">
            <p className="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-teal-400">
              {lang === "uz" ? "AI TELEFON YORDAMCHI" : "AI ТЕЛЕФОННЫЙ АССИСТЕНТ"}
            </p>
            <h2 className="text-[2rem] font-extrabold leading-tight text-white">{t.ai.title}</h2>
            <p className="mt-3 text-[15px] leading-relaxed text-gray-300">{t.ai.sub}</p>

            <div className="mt-6 grid grid-cols-2 gap-2.5">
              {badgeLabels.map((b, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2.5 rounded-xl bg-white/6 px-3.5 py-2.5 ring-1 ring-white/8 transition-colors hover:bg-white/10"
                >
                  <span className="pulse-dot h-1.5 w-1.5 shrink-0 rounded-full bg-teal-400" style={{ animationDelay: `${i * 0.5}s` }} />
                  <span className="text-[13px] text-gray-300">{b}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-xl bg-white/5 p-4 text-[12px] leading-relaxed text-gray-400 ring-1 ring-white/8">
              <span className="mr-1.5 font-bold text-teal-400">⚠</span>
              {t.ai.safety}
            </div>

            <button
              data-chat-trigger
              className="mt-7 inline-flex items-center gap-2.5 rounded-full bg-teal-500 px-6 py-2.5 text-sm font-semibold text-white transition-all hover:bg-teal-400 hover:shadow-lg hover:shadow-teal-900/40 active:scale-95"
            >
              <span className="pulse-dot h-2 w-2 rounded-full bg-white/70" />
              {t.ai.btn}
            </button>
          </Anim>

          {/* Right: call flow steps card */}
          <Anim delay={160} from="right">
            <div ref={ref} className="overflow-hidden rounded-2xl bg-white shadow-2xl">
              <div className="border-b border-gray-100 px-6 py-4">
                <p className="font-semibold text-gray-900">
                  {lang === "uz" ? "Qo'ng'iroq oqimi" : "Процесс звонка"}
                </p>
              </div>
              <div className="px-6 py-5">
                {flowSteps.map((step, i) => (
                  <div key={i} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-all duration-500 ${
                          i < 3
                            ? "bg-teal-500 text-white shadow-sm shadow-teal-200"
                            : "bg-gray-100 text-gray-400"
                        }`}
                        style={{
                          transform: visible ? "scale(1)" : "scale(0.7)",
                          transition: `transform 0.45s cubic-bezier(0.22,1,0.36,1) ${i * 120}ms`,
                        }}
                      >
                        {i + 1}
                      </div>
                      {i < flowSteps.length - 1 && (
                        <div
                          className={`draw-line my-1 w-0.5 rounded-full ${i < 2 ? "bg-teal-200" : "bg-gray-100"}`}
                          style={{ height: 28, animationDelay: `${i * 120 + 200}ms` }}
                        />
                      )}
                    </div>
                    <div className="pb-5 pt-0.5">
                      <p className={`text-[14px] font-semibold ${i < 3 ? "text-gray-900" : "text-gray-400"}`}>
                        {step}
                      </p>
                      <p className="mt-0.5 text-xs text-gray-400">{flowSub}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Anim>

        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// DOCTORS
// ─────────────────────────────────────────────────────────

const AVATAR_COLORS = [
  { outer: "bg-teal-100",  inner: "bg-teal-400"  },
  { outer: "bg-blue-100",  inner: "bg-blue-400"  },
  { outer: "bg-teal-50",   inner: "bg-teal-300"  },
];

function Doctors() {
  const { t, lang } = useT();
  return (
    <section id="doctors" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Anim className="mb-12">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-teal-500">
            {lang === "uz" ? "SHIFOKORLAR" : "ВРАЧИ"}
          </p>
          <h2 className="text-[2rem] font-extrabold text-gray-900">{t.doctors.title}</h2>
          <p className="mt-3 text-[15px] text-gray-500">{t.doctors.sub}</p>
        </Anim>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {t.doctors.cards.map((doc, i) => (
            <Anim key={i} delay={i * 80} from="bottom">
              <div className="group flex flex-col items-start rounded-2xl bg-white p-6 ring-1 ring-gray-100 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:ring-teal-100">
                {/* Avatar */}
                <div className={`mb-5 flex h-20 w-20 items-center justify-center rounded-full ${AVATAR_COLORS[i].outer} transition-transform duration-300 group-hover:scale-105`}>
                  <div className={`h-12 w-12 rounded-full ${AVATAR_COLORS[i].inner}`} />
                </div>
                <p className="font-bold text-[15px] text-gray-900">{doc.name}</p>
                <p className="mt-0.5 text-sm font-medium text-teal-600">{doc.spec}</p>
                <div className="mt-3 space-y-1.5 text-xs text-gray-500">
                  <p>{doc.exp}</p>
                  <p>{doc.sched}</p>
                </div>
                <a
                  href="/yozilish"
                  className="mt-5 block w-full rounded-full bg-teal-500 py-2.5 text-center text-sm font-semibold text-white transition-all hover:bg-teal-600 active:scale-95"
                >
                  {t.doctors.btn}
                </a>
              </div>
            </Anim>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// PROCESS
// ─────────────────────────────────────────────────────────

function Process() {
  const { t, lang } = useT();
  return (
    <section className="bg-[#F8FAFC] py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Anim className="mb-12">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-teal-500">
            {lang === "uz" ? "JARAYON" : "ПРОЦЕСС"}
          </p>
          <h2 className="text-[2rem] font-extrabold text-gray-900">{t.flow.title}</h2>
          <p className="mt-3 text-[15px] text-gray-500">{t.flow.sub}</p>
        </Anim>
        <div className="grid gap-4 sm:grid-cols-3">
          {t.flow.steps.map((step, i) => (
            <Anim key={i} delay={i * 90} from="bottom">
              <div className="group h-full rounded-2xl bg-white p-6 ring-1 ring-gray-100 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md hover:ring-teal-100">
                <p className="text-5xl font-extrabold text-gray-100 transition-colors duration-300 group-hover:text-teal-50">
                  0{i + 1}
                </p>
                <p className="mt-3 font-bold text-[15px] text-gray-900">{step.title}</p>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{step.desc}</p>
              </div>
            </Anim>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// FAQ + CONTACT
// ─────────────────────────────────────────────────────────

function ContactSection() {
  const { t, lang } = useT();
  const [form, setForm]   = useState({ name: "", phone: "", msg: "" });
  const [sent, setSent]   = useState(false);
  const [busy, setBusy]   = useState(false);
  const [err, setErr]     = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await createPublicCallback({ name: form.name.trim(), phone: form.phone.trim(), message: form.msg.trim() || undefined });
      setSent(true);
    } catch (e2) {
      const code = e2 instanceof BookingApiError ? e2.code : "";
      setErr(
        code === "invalid_phone"
          ? (lang === "uz" ? "Telefon raqam noto'g'ri. +998 bilan kiriting." : "Неверный номер. Введите с +998.")
          : code === "rate_limited"
            ? (lang === "uz" ? "Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring." : "Слишком много попыток. Повторите позже.")
            : (lang === "uz" ? "Xatolik yuz berdi. Qayta urinib ko'ring." : "Произошла ошибка. Повторите попытку."),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section id="faq" className="bg-white py-20 sm:py-24">
      <span id="contact" className="block -mt-20 pt-20 pointer-events-none" />
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <Anim className="mb-12">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-teal-500">
            {lang === "uz" ? "ALOQA" : "КОНТАКТЫ"}
          </p>
          <h2 className="text-[2rem] font-extrabold text-gray-900">
            {lang === "uz" ? "Savollar va qabulga yozilish" : "Вопросы и запись на приём"}
          </h2>
        </Anim>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* FAQ */}
          <Anim from="left">
            <div className="rounded-2xl bg-white ring-1 ring-gray-100 shadow-sm overflow-hidden">
              {t.faq.items.map((item, i) => (
                <div
                  key={i}
                  className={i < t.faq.items.length - 1 ? "border-b border-gray-50" : ""}
                >
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="flex w-full items-start justify-between gap-4 px-6 py-4 text-left transition-colors hover:bg-gray-50/70"
                  >
                    <span className={`text-[14px] font-semibold leading-snug transition-colors ${openFaq === i ? "text-teal-600" : "text-gray-900"}`}>
                      {item.q}
                    </span>
                    <svg
                      viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
                      className={`mt-0.5 h-4 w-4 shrink-0 text-gray-300 transition-transform duration-300 ${openFaq === i ? "rotate-180 text-teal-400" : ""}`}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>
                  <div
                    style={{
                      maxHeight: openFaq === i ? "200px" : "0",
                      opacity:   openFaq === i ? 1 : 0,
                      overflow:  "hidden",
                      transition: "max-height 0.38s cubic-bezier(0.22,1,0.36,1), opacity 0.3s ease",
                    }}
                  >
                    <p className="px-6 pb-4 text-[13px] leading-relaxed text-teal-600">
                      {item.a}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Anim>

          {/* Booking form */}
          <Anim delay={120} from="right">
            {sent ? (
              <div className="flex h-full min-h-[320px] items-center justify-center rounded-2xl bg-teal-50 ring-1 ring-teal-100">
                <div className="text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-teal-100">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="h-7 w-7 text-teal-600">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                  <p className="text-sm font-semibold text-teal-800">{t.contact.fSent}</p>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl bg-white ring-1 ring-gray-100 shadow-sm">
                <div className="border-b border-gray-100 px-6 py-4">
                  <p className="font-semibold text-gray-900">
                    {lang === "uz" ? "Qabulga yozilish" : "Записаться на приём"}
                  </p>
                </div>
                <form onSubmit={submit} className="space-y-4 p-6">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500">{t.contact.fName}</label>
                    <input
                      type="text" required value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-50"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500">{t.contact.fPhone}</label>
                    <input
                      type="tel" required value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-50"
                    />
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-gray-500">{t.contact.fMsg}</label>
                    <textarea
                      rows={3} value={form.msg}
                      onChange={(e) => setForm({ ...form, msg: e.target.value })}
                      className="w-full resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-50"
                    />
                  </div>
                  {err && <p className="text-sm text-red-600">{err}</p>}
                  <button
                    type="submit"
                    disabled={busy}
                    className="w-full rounded-full bg-teal-500 py-3 text-sm font-semibold text-white transition-all hover:bg-teal-600 hover:shadow-md hover:shadow-teal-200 active:scale-[0.98] disabled:opacity-60"
                  >
                    {busy
                      ? (lang === "uz" ? "Yuborilmoqda..." : "Отправка...")
                      : (lang === "uz" ? "So'rov yuborish" : "Отправить запрос")}
                  </button>
                </form>
              </div>
            )}
          </Anim>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────
// FOOTER
// ─────────────────────────────────────────────────────────

function Footer() {
  const { t } = useT();
  return (
    <footer className="text-gray-400" style={{ backgroundColor: "#071820" }}>
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-500">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.5} className="h-4 w-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12M6 12h12" />
            </svg>
          </div>
          <span className="font-bold text-white">
            UroClinic <span className="text-teal-400">AI</span>
          </span>
        </div>
        <p className="mt-4 max-w-lg text-sm leading-relaxed text-gray-500">{t.footer.safety}</p>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/5 pt-5 text-xs">
          <span className="text-gray-600">{t.footer.copy}</span>
          <div className="flex items-center gap-4">
            <a href="/login" className="text-gray-600 transition-colors hover:text-gray-400">{t.footer.staff}</a>
            <a href="#" className="text-gray-600 transition-colors hover:text-gray-400">{t.footer.privacy}</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

// ─────────────────────────────────────────────────────────
// PAGE ROOT
// ─────────────────────────────────────────────────────────

export default function ClinicLanding() {
  const [lang, setLang] = useState<Lang>("uz");
  const t = translations[lang];

  return (
    <LangCtx.Provider value={{ lang, setLang, t }}>
      <ScrollProgress />
      <div className="min-h-screen bg-white text-gray-900">
        <Header />
        <main>
          <Hero />
          <Trust />
          <Services />
          <AISection />
          <Doctors />
          <Process />
          <ContactSection />
        </main>
        <Footer />
        <ChatWidget />
      </div>
    </LangCtx.Provider>
  );
}
