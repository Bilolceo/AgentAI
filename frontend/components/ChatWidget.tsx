"use client";

import { useEffect, useRef, useState } from "react";
import { startCall, sendMessage } from "@/lib/api";
import { createPublicCallback, BookingApiError } from "@/lib/public-booking";
import type { ChatTurn } from "@/lib/types";

type Lang = "uz" | "ru";
type Turn = ChatTurn & { fresh?: boolean };

const STORAGE_KEY = "clinic_chat_v1";

const STR = {
  uz: {
    title: "AI Yordamchi",
    online: "Onlayn",
    greeting:
      "Salom! Men klinikamizning AI yordamchisiman. Xizmatlar, ish vaqti yoki qabulga yozilish bo'yicha yordam bera olaman.",
    placeholder: "Xabar yozing...",
    open: "Chat ochish",
    close: "Yopish",
    reset: "Yangi suhbat",
    connError: "Ulanishda xatolik yuz berdi. Qayta urinib ko'ring.",
    sendError: "Xabar yuborishda xatolik.",
    emergency: "Shoshilinch holat — 103 raqamiga qo'ng'iroq qiling",
    transfer: "Operatorimiz tez orada siz bilan bog'lanadi",
    chips: { hours: "Ish vaqti", prices: "Narxlar", address: "Manzil", book: "Qabulga yozilish" },
    msgHours: "Ish vaqtingiz qanday?",
    msgPrices: "Xizmatlar narxi qancha?",
    msgAddress: "Manzilingiz qayerda?",
    bookTitle: "Qabulga yozilish",
    bookHint: "Ism va telefoningizni qoldiring — operatorimiz bog'lanadi.",
    fName: "Ismingiz",
    fPhone: "Telefon (+998...)",
    fSubmit: "Yuborish",
    fSending: "Yuborilmoqda...",
    fCancel: "Bekor qilish",
    fOk: "Rahmat! So'rovingiz qabul qilindi. Operatorimiz tez orada siz bilan bog'lanadi.",
    fBad: "Telefon raqam noto'g'ri. Iltimos, +998 bilan kiriting.",
    fRate: "Juda ko'p urinish. Birozdan so'ng qayta urinib ko'ring.",
    fErr: "Xatolik yuz berdi. Qayta urinib ko'ring.",
    disclaimer: "AI diagnoz qo'ymaydi. Tibbiy savollar shifokorga yo'naltiriladi.",
  },
  ru: {
    title: "AI-ассистент",
    online: "Онлайн",
    greeting:
      "Здравствуйте! Я AI-ассистент клиники. Помогу с услугами, графиком работы или записью на приём.",
    placeholder: "Напишите сообщение...",
    open: "Открыть чат",
    close: "Закрыть",
    reset: "Новый диалог",
    connError: "Ошибка подключения. Попробуйте ещё раз.",
    sendError: "Ошибка отправки сообщения.",
    emergency: "Экстренный случай — позвоните 103",
    transfer: "Наш оператор скоро свяжется с вами",
    chips: { hours: "График", prices: "Цены", address: "Адрес", book: "Записаться" },
    msgHours: "Какой у вас график работы?",
    msgPrices: "Сколько стоят услуги?",
    msgAddress: "Где вы находитесь?",
    bookTitle: "Записаться на приём",
    bookHint: "Оставьте имя и телефон — оператор свяжется с вами.",
    fName: "Ваше имя",
    fPhone: "Телефон (+998...)",
    fSubmit: "Отправить",
    fSending: "Отправка...",
    fCancel: "Отмена",
    fOk: "Спасибо! Заявка принята. Наш оператор скоро свяжется с вами.",
    fBad: "Неверный номер. Пожалуйста, введите с +998.",
    fRate: "Слишком много попыток. Повторите позже.",
    fErr: "Произошла ошибка. Повторите попытку.",
    disclaimer: "AI не ставит диагноз. Медицинские вопросы направляются врачу.",
  },
} as const;

function TypewriterText({ text, animate }: { text: string; animate?: boolean }) {
  const [shown, setShown] = useState(animate ? "" : text);
  useEffect(() => {
    if (!animate) {
      setShown(text);
      return;
    }
    let i = 0;
    setShown("");
    const step = Math.max(12, Math.round(text.length / 40));
    const id = setInterval(() => {
      i += step;
      setShown(text.slice(0, i));
      if (i >= text.length) {
        setShown(text);
        clearInterval(id);
      }
    }, 24);
    return () => clearInterval(id);
  }, [text, animate]);
  return <>{shown}</>;
}

export function ChatWidget({ lang = "uz" }: { lang?: Lang }) {
  const t = STR[lang];
  const [open, setOpen] = useState(false);
  const [callId, setCallId] = useState<number | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState(false);
  const [bForm, setBForm] = useState({ name: "", phone: "" });
  const [bBusy, setBBusy] = useState(false);
  const [bErr, setBErr] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const restored = useRef(false);

  // Restore previous conversation once.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const saved = JSON.parse(raw) as { callId: number | null; turns: Turn[] };
        if (saved?.turns?.length) {
          setTurns(saved.turns.map((x) => ({ ...x, fresh: false })));
          setCallId(saved.callId ?? null);
          restored.current = true;
        }
      }
    } catch {
      /* ignore corrupt storage */
    }
  }, []);

  // Persist conversation.
  useEffect(() => {
    if (turns.length === 0) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ callId, turns }));
    } catch {
      /* ignore quota */
    }
  }, [turns, callId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, busy, booking]);

  useEffect(() => {
    if (open && callId === null && turns.length === 0 && !restored.current) {
      initCall();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  async function initCall() {
    setBusy(true);
    setError(null);
    try {
      const res = await startCall("+998000000000");
      setCallId(res.call_id);
      // Use our localized greeting so it matches the page language (the backend
      // mock returns a bilingual greeting which looks unpolished).
      setTurns([{ role: "assistant", text: t.greeting, fresh: true }]);
    } catch {
      setError(t.connError);
    } finally {
      setBusy(false);
    }
  }

  async function ensureCall(): Promise<number | null> {
    if (callId !== null) return callId;
    try {
      const res = await startCall("+998000000000");
      setCallId(res.call_id);
      return res.call_id;
    } catch {
      setError(t.connError);
      return null;
    }
  }

  async function pushUserMessage(message: string) {
    const trimmed = message.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError(null);
    setTurns((arr) => [...arr, { role: "user", text: trimmed }]);
    const id = await ensureCall();
    if (id === null) {
      setBusy(false);
      return;
    }
    try {
      const res = await sendMessage(id, trimmed);
      setTurns((arr) => [
        ...arr,
        { role: "assistant", text: res.reply, action: res.action, transferred: res.transferred, fresh: true },
      ]);
    } catch {
      setError(t.sendError);
    } finally {
      setBusy(false);
    }
  }

  function onSend() {
    const v = text.trim();
    if (!v) return;
    setText("");
    pushUserMessage(v);
  }

  async function submitBooking(e: React.FormEvent) {
    e.preventDefault();
    setBBusy(true);
    setBErr(null);
    try {
      await createPublicCallback({
        name: bForm.name.trim(),
        phone: bForm.phone.trim(),
        message: lang === "uz" ? "Onlayn chat orqali so'rov" : "Заявка через онлайн-чат",
      });
      setBooking(false);
      setBForm({ name: "", phone: "" });
      setTurns((arr) => [...arr, { role: "assistant", text: t.fOk, fresh: true }]);
    } catch (e2) {
      const code = e2 instanceof BookingApiError ? e2.code : "";
      setBErr(code === "invalid_phone" ? t.fBad : code === "rate_limited" ? t.fRate : t.fErr);
    } finally {
      setBBusy(false);
    }
  }

  function resetChat() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    restored.current = false;
    setTurns([]);
    setCallId(null);
    setError(null);
    setBooking(false);
    initCall();
  }

  const showChips = !booking && turns.length > 0 && turns.length < 8;

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          data-chat-trigger
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-xl hover:bg-blue-700 transition-all hover:scale-105 active:scale-95"
          aria-label={t.open}
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-7 w-7">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
          </svg>
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-green-500 text-[10px] font-bold">AI</span>
        </button>
      )}

      {/* Chat panel — full-screen sheet on mobile, floating card on sm+ */}
      {open && (
        <div className="fixed inset-x-0 bottom-0 z-50 flex h-[88vh] flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl ring-1 ring-gray-200 sm:inset-auto sm:bottom-6 sm:right-6 sm:h-[560px] sm:w-[380px] sm:rounded-2xl">
          {/* Header */}
          <div className="flex shrink-0 items-center justify-between bg-blue-600 px-4 py-3 text-white">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                </svg>
              </div>
              <div>
                <div className="text-sm font-semibold leading-tight">{t.title}</div>
                <div className="flex items-center gap-1 text-xs text-white/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                  {t.online}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={resetChat}
                className="flex h-7 w-7 items-center justify-center rounded-full transition-colors hover:bg-white/20"
                aria-label={t.reset}
                title={t.reset}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
              </button>
              <button
                onClick={() => setOpen(false)}
                className="flex h-7 w-7 items-center justify-center rounded-full transition-colors hover:bg-white/20"
                aria-label={t.close}
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {busy && turns.length === 0 && <TypingBubble />}

            {turns.map((turn, i) => (
              <div key={i} className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={
                    "max-w-[82%] rounded-2xl px-3 py-2 text-sm leading-relaxed " +
                    (turn.role === "user" ? "rounded-br-sm bg-blue-600 text-white" : "rounded-bl-sm bg-gray-100 text-gray-900")
                  }
                >
                  {turn.role === "assistant" ? <TypewriterText text={turn.text} animate={turn.fresh} /> : turn.text}
                  {turn.action === "emergency" && (
                    <div className="mt-2 rounded-lg border border-red-200 bg-red-50 px-2 py-1.5 text-xs font-medium text-red-700">
                      {t.emergency}
                    </div>
                  )}
                  {turn.action === "transfer" && (
                    <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2 py-1.5 text-xs font-medium text-amber-700">
                      {t.transfer}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {busy && turns.length > 0 && <TypingBubble />}

            {/* Quick-reply chips */}
            {showChips && (
              <div className="flex flex-wrap gap-2 pt-1">
                <Chip onClick={() => pushUserMessage(t.msgHours)} disabled={busy}>{t.chips.hours}</Chip>
                <Chip onClick={() => pushUserMessage(t.msgPrices)} disabled={busy}>{t.chips.prices}</Chip>
                <Chip onClick={() => pushUserMessage(t.msgAddress)} disabled={busy}>{t.chips.address}</Chip>
                <Chip primary onClick={() => setBooking(true)} disabled={busy}>{t.chips.book}</Chip>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {error && <div className="shrink-0 px-4 pb-1 text-xs text-red-500">{error}</div>}

          {/* Booking mini-form OR input */}
          {booking ? (
            <form onSubmit={submitBooking} className="shrink-0 space-y-2 border-t bg-gray-50 p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-gray-900">{t.bookTitle}</p>
                <button type="button" onClick={() => setBooking(false)} className="text-xs text-gray-400 hover:text-gray-600">
                  {t.fCancel}
                </button>
              </div>
              <p className="text-xs text-gray-500">{t.bookHint}</p>
              <input
                className="w-full rounded-xl border bg-white px-3 py-2 text-sm outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500"
                value={bForm.name}
                onChange={(e) => setBForm((f) => ({ ...f, name: e.target.value }))}
                placeholder={t.fName}
                required
              />
              <input
                className="w-full rounded-xl border bg-white px-3 py-2 text-sm outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500"
                value={bForm.phone}
                onChange={(e) => setBForm((f) => ({ ...f, phone: e.target.value }))}
                placeholder={t.fPhone}
                inputMode="tel"
                required
              />
              {bErr && <p className="text-xs text-red-500">{bErr}</p>}
              <button
                type="submit"
                disabled={bBusy || !bForm.name.trim() || !bForm.phone.trim()}
                className="w-full rounded-xl bg-blue-600 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-40"
              >
                {bBusy ? t.fSending : t.fSubmit}
              </button>
            </form>
          ) : (
            <div className="shrink-0 border-t bg-gray-50 p-3">
              <div className="flex gap-2">
                <input
                  className="flex-1 rounded-xl border bg-white px-3 py-2 text-sm outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && onSend()}
                  placeholder={t.placeholder}
                  disabled={busy && turns.length === 0}
                />
                <button
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:opacity-40"
                  onClick={onSend}
                  disabled={busy || !text.trim()}
                  aria-label={t.fSubmit}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="h-4 w-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
                  </svg>
                </button>
              </div>
              <p className="mt-1.5 px-1 text-[10px] leading-snug text-gray-400">{t.disclaimer}</p>
            </div>
          )}
        </div>
      )}
    </>
  );
}

function TypingBubble() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
        <div className="flex gap-1.5">
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "150ms" }} />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}

function Chip({ children, onClick, disabled, primary }: { children: React.ReactNode; onClick: () => void; disabled?: boolean; primary?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={
        "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 " +
        (primary
          ? "border-blue-600 bg-blue-600 text-white hover:bg-blue-700"
          : "border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:text-blue-600")
      }
    >
      {children}
    </button>
  );
}
