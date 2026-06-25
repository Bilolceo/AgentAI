"use client";

import { useEffect, useRef, useState } from "react";
import { getManagerActionItems, getManagerSchedule } from "@/lib/manager";
import { useLanguage } from "@/lib/i18n";
import { IconBell } from "@/components/icons";

type Notif = { id: string; typeKey: string; detail: string };

const SEEN_KEY = "rahbar_seen_notifs";

function loadSeen(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveSeen(s: Set<string>): void {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify([...s]));
  } catch {
    // ignore
  }
}

// Derived notification feed (M2 MVP): callbacks + today's operator-required /
// cancelled appointments. A dedicated notification entity is a future task.
export function NotificationBell() {
  const { t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [notifs, setNotifs] = useState<Notif[]>([]);
  const [seen, setSeen] = useState<Set<string>>(new Set());
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSeen(loadSeen());
  }, []);

  useEffect(() => {
    function build() {
      Promise.all([getManagerActionItems(), getManagerSchedule({})])
        .then(([items, sched]) => {
          const out: Notif[] = [];
          for (const it of items) {
            out.push({
              id: `cb-${it.id}`,
              typeKey: it.reason === "operator_request" ? "ntype_operator_required" : "ntype_callback_required",
              detail: it.phone_masked ?? "-",
            });
          }
          for (const a of sched) {
            const when = `${a.scheduled_at?.slice(11, 16) ?? ""} ${a.patient_short ?? ""}`.trim();
            if (a.operator_required) out.push({ id: `op-${a.id}`, typeKey: "ntype_operator_required", detail: when });
            if (a.status === "cancelled") out.push({ id: `ca-${a.id}`, typeKey: "ntype_appt_cancelled", detail: when });
          }
          setNotifs(out);
        })
        .catch(() => {});
    }
    build();
    const iv = setInterval(build, 30000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const unread = notifs.filter((n) => !seen.has(n.id)).length;

  function markAll() {
    const s = new Set(notifs.map((n) => n.id));
    setSeen(s);
    saveSeen(s);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={t("notif_bell")}
        className="relative flex items-center gap-1.5 rounded border border-slate-300 px-2 py-1.5 text-sm text-slate-700 hover:bg-slate-100 sm:px-2.5"
      >
        <IconBell width={18} height={18} />
        <span className="hidden sm:inline">{t("notif_bell")}</span>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold text-white">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2 text-sm font-medium text-slate-700">
            {t("notif_bell")}
            {notifs.length > 0 && (
              <button onClick={markAll} className="text-xs text-blue-600 hover:underline">
                {t("notif_mark_all")}
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifs.length === 0 ? (
              <div className="p-4 text-sm text-slate-400">{t("notif_none")}</div>
            ) : (
              notifs.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-2 border-b border-slate-50 px-3 py-2 text-sm ${seen.has(n.id) ? "opacity-60" : ""}`}
                >
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-amber-500" />
                  <div className="min-w-0">
                    <div className="font-medium text-slate-700">{t(n.typeKey)}</div>
                    <div className="truncate text-xs text-slate-500">{n.detail}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
