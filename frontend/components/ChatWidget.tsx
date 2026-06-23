"use client";

import { useEffect, useRef, useState } from "react";
import { startCall, sendMessage } from "@/lib/api";
import type { ChatTurn } from "@/lib/types";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [callId, setCallId] = useState<number | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  useEffect(() => {
    if (open && callId === null && turns.length === 0) {
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
      const greeting =
        res.greeting ||
        "Salom! Men klinikamizning AI yordamchisiman. Sizga qanday yordam bera olaman?";
      setTurns([{ role: "assistant", text: greeting }]);
    } catch {
      setError("Ulanishda xatolik yuz berdi. Qayta urinib ko'ring.");
    } finally {
      setBusy(false);
    }
  }

  async function onSend() {
    const trimmed = text.trim();
    if (!trimmed || busy || callId === null) return;
    setBusy(true);
    setError(null);
    setTurns((t) => [...t, { role: "user", text: trimmed }]);
    setText("");
    try {
      const res = await sendMessage(callId, trimmed);
      setTurns((t) => [
        ...t,
        { role: "assistant", text: res.reply, action: res.action, transferred: res.transferred },
      ]);
    } catch {
      setError("Xabar yuborishda xatolik.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {/* Floating button */}
      {!open && (
        <button
          data-chat-trigger
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-xl hover:bg-blue-700 transition-all hover:scale-105 active:scale-95"
          aria-label="Chat ochish"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="h-7 w-7"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z"
            />
          </svg>
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-green-500 text-[10px] font-bold">
            AI
          </span>
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-6 right-6 z-50 flex w-[360px] flex-col rounded-2xl bg-white shadow-2xl ring-1 ring-gray-200 overflow-hidden" style={{ height: 500 }}>
          {/* Header */}
          <div className="flex items-center justify-between bg-blue-600 px-4 py-3 text-white shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="h-5 w-5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z"
                  />
                </svg>
              </div>
              <div>
                <div className="text-sm font-semibold leading-tight">AI Yordamchi</div>
                <div className="flex items-center gap-1 text-xs text-white/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                  Onlayn
                </div>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-white/20 transition-colors"
              aria-label="Yopish"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                className="h-4 w-4"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {busy && turns.length === 0 && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
                  <div className="flex gap-1.5">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "150ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            {turns.map((turn, i) => (
              <div key={i} className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={
                    "max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed " +
                    (turn.role === "user"
                      ? "rounded-br-sm bg-blue-600 text-white"
                      : "rounded-bl-sm bg-gray-100 text-gray-900")
                  }
                >
                  {turn.text}
                  {turn.action === "emergency" && (
                    <div className="mt-2 rounded-lg bg-red-50 border border-red-200 px-2 py-1.5 text-xs font-medium text-red-700">
                      ⚠️ Shoshilinch holat — 103 raqamiga qo'ng'iroq qiling
                    </div>
                  )}
                  {turn.action === "transfer" && (
                    <div className="mt-2 rounded-lg bg-amber-50 border border-amber-200 px-2 py-1.5 text-xs font-medium text-amber-700">
                      Operatorimiz tez orada siz bilan bog'lanadi
                    </div>
                  )}
                </div>
              </div>
            ))}

            {busy && turns.length > 0 && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
                  <div className="flex gap-1.5">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "150ms" }} />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {error && (
            <div className="shrink-0 px-4 pb-1 text-xs text-red-500">{error}</div>
          )}

          {/* Input */}
          <div className="shrink-0 flex gap-2 border-t bg-gray-50 p-3">
            <input
              className="flex-1 rounded-xl border bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSend()}
              placeholder="Xabar yozing..."
              disabled={busy && turns.length === 0}
            />
            <button
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 transition-colors"
              onClick={onSend}
              disabled={busy || !text.trim()}
              aria-label="Yuborish"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                className="h-4 w-4"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
