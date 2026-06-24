"use client";

import { useEffect, useState } from "react";
import { getManagerActionItems, getManagerSchedule } from "@/lib/manager";
import type { ManagerActionItem, ManagerAppointment } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { Card, CardBody, Badge, LoadingState, ErrorState, EmptyState } from "@/components/ui";

type Priority = "urgent" | "high" | "medium" | "low";
type Notif = { id: string; typeKey: string; priority: Priority; detail: string };

// Shared with NotificationBell so marking read here also clears the bell badge.
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

function tone(p: Priority): "danger" | "warning" | "info" | "neutral" {
  return p === "urgent" ? "danger" : p === "high" ? "warning" : p === "medium" ? "info" : "neutral";
}

function derive(items: ManagerActionItem[], sched: ManagerAppointment[]): Notif[] {
  const out: Notif[] = [];
  for (const it of items) {
    out.push({
      id: `cb-${it.id}`,
      typeKey: it.reason === "operator_request" ? "ntype_operator_required" : "ntype_callback_required",
      priority: (it.priority as Priority) || "medium",
      detail: it.phone_masked ?? "-",
    });
  }
  for (const a of sched) {
    const when = `${a.scheduled_at?.slice(11, 16) ?? ""} ${a.patient_short ?? ""}`.trim();
    if (a.operator_required) out.push({ id: `op-${a.id}`, typeKey: "ntype_operator_required", priority: "high", detail: when });
    if (a.status === "cancelled") out.push({ id: `ca-${a.id}`, typeKey: "ntype_appt_cancelled", priority: "medium", detail: when });
  }
  return out;
}

export default function RahbarNotifications() {
  const { t } = useLanguage();
  const [notifs, setNotifs] = useState<Notif[]>([]);
  const [read, setRead] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRead(loadSeen());
  }, []);

  function markRead(ids: string[]) {
    setRead((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => next.add(id));
      saveSeen(next);
      return next;
    });
  }

  useEffect(() => {
    Promise.all([getManagerActionItems(), getManagerSchedule({})])
      .then(([items, sched]) => setNotifs(derive(items, sched)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const unread = notifs.filter((n) => !read.has(n.id)).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-500">{unread} {t("mgr_unread")}</p>
        {notifs.length > 0 && (
          <button className="rounded-lg border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-100" onClick={() => markRead(notifs.map((n) => n.id))}>
            {t("mgr_mark_all_read")}
          </button>
        )}
      </div>
      {notifs.length === 0 ? (
        <EmptyState title={t("mgr_notif_empty")} />
      ) : (
        <div className="space-y-2">
          {notifs.map((n) => (
            <Card key={n.id} className={read.has(n.id) ? "opacity-60" : ""}>
              <CardBody className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Badge tone={tone(n.priority)}>{t(n.typeKey)}</Badge>
                  <span className="font-mono text-sm text-slate-700">{n.detail}</span>
                </div>
                {!read.has(n.id) && (
                  <button className="text-xs text-blue-600 hover:underline" onClick={() => markRead([n.id])}>
                    {t("mgr_mark_read")}
                  </button>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
