"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getManagerSchedule,
  getManagerDoctors,
  getManagerLeads,
  createManagerAppointment,
  setManagerAppointmentStatus,
  deleteManagerAppointment,
} from "@/lib/manager";
import type { ManagerAppointment, ManagerDoctorWorkload } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { Card, CardBody, CardHeader, StatusBadge, Badge, LoadingState, ErrorState } from "@/components/ui";
import { StatTile, color, statusColor } from "@/components/charts";
import { WeekCalendar, startOfWeek, addDays, ymd } from "@/components/calendar";
import { IconPlus } from "@/components/icons";

const LEGEND_STATUSES = ["confirmed", "pending", "cancelled", "arrived", "operator_required"];
type ListFilter = "all" | "confirmed" | "cancelled";

export default function RahbarHome() {
  const { t, tStatus } = useLanguage();
  const [weekStart, setWeekStart] = useState<Date>(startOfWeek(new Date()));
  const [appts, setAppts] = useState<ManagerAppointment[]>([]);
  const [doctors, setDoctors] = useState<ManagerDoctorWorkload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [picked, setPicked] = useState<ManagerAppointment | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [acting, setActing] = useState(false);
  const [actErr, setActErr] = useState<string | null>(null);
  const [listFilter, setListFilter] = useState<ListFilter | null>(null);
  const [view, setView] = useState<"agenda" | "calendar">("agenda");
  const [leads, setLeads] = useState<ManagerAppointment[]>([]);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getManagerSchedule({ from: ymd(weekStart), to: ymd(addDays(weekStart, 6)) })
      .then(setAppts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [weekStart]);

  const loadLeads = useCallback(() => {
    getManagerLeads().then(setLeads).catch(() => setLeads([]));
  }, []);

  useEffect(load, [load]);
  useEffect(() => {
    getManagerDoctors().then(setDoctors).catch(() => setDoctors([]));
    loadLeads();
  }, [loadLeads]);

  async function changeStatus(id: number, status: string) {
    setActing(true);
    setActErr(null);
    try {
      const updated = await setManagerAppointmentStatus(id, status);
      setPicked(updated);
      setMessage(t("appt_status_updated"));
      load();
      loadLeads();
    } catch (e) {
      setActErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setActing(false);
    }
  }

  async function removeAppt(id: number) {
    if (!window.confirm(t("appt_delete_confirm"))) return;
    setActing(true);
    setActErr(null);
    try {
      await deleteManagerAppointment(id);
      setPicked(null);
      setMessage(t("appt_deleted"));
      load();
      loadLeads();
    } catch (e) {
      setActErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setActing(false);
    }
  }

  const dayLabels = [
    t("dow_mon"), t("dow_tue"), t("dow_wed"), t("dow_thu"), t("dow_fri"), t("dow_sat"), t("dow_sun"),
  ];
  const weekRange = `${ymd(weekStart)} - ${ymd(addDays(weekStart, 6))}`;

  // All KPIs are derived from the loaded week, so they always agree with the
  // calendar below (no mixing of "today" and "this week" scopes).
  const isPending = (a: ManagerAppointment) => a.status === "pending" || a.status === "new";
  const pending = appts.filter(isPending).sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""));
  const confirmedCount = appts.filter((a) => a.status === "confirmed").length;
  // Single "needs your action" feed: online requests (no time yet) + unconfirmed
  // appointments. Leads have no scheduled_at, so they sort to the top.
  const actionItems = [...leads, ...pending].sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""));

  function listMatch(a: ManagerAppointment, f: ListFilter): boolean {
    if (f === "confirmed") return a.status === "confirmed";
    if (f === "cancelled") return a.status === "cancelled";
    return true;
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-500">{t("rahbar_home_sub")}</p>
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
        >
          <IconPlus width={16} height={16} /> {t("new_appt")}
        </button>
      </div>
      {message && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">{message}</div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <KpiButton onClick={() => actionItems.length && document.getElementById("action-card")?.scrollIntoView({ behavior: "smooth" })}>
          <StatTile label={t("kpi_pending")} value={actionItems.length} accent="amber" />
        </KpiButton>
        <KpiButton onClick={() => setListFilter("all")}>
          <StatTile label={t("kpi_week_total")} value={appts.length} accent="indigo" />
        </KpiButton>
        <KpiButton onClick={() => setListFilter("confirmed")}>
          <StatTile label={t("mgr_kpi_confirmed")} value={confirmedCount} accent="emerald" />
        </KpiButton>
      </div>

      {/* One clear "needs your action" list: online requests + unconfirmed
          appointments, each with one-tap confirm / cancel. */}
      <div id="action-card">
        <Card className="border-amber-300 ring-1 ring-amber-100">
          <CardHeader title={t("rahbar_action_title")} subtitle={t("rahbar_action_hint")} />
          <CardBody className="space-y-2">
            {actionItems.length === 0 ? (
              <p className="py-3 text-center text-sm text-slate-400">{t("rahbar_action_empty")}</p>
            ) : (
              actionItems.map((a) => (
                <ActionRow
                  key={a.id}
                  a={a}
                  t={t}
                  acting={acting}
                  onConfirm={() => changeStatus(a.id, "confirmed")}
                  onCancel={() => changeStatus(a.id, "cancelled")}
                  onOpen={() => setPicked(a)}
                />
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader
          title={t("rahbar_nav_calendar")}
          subtitle={weekRange}
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex overflow-hidden rounded-lg border border-slate-300 text-xs">
                {(["agenda", "calendar"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    className={`px-2.5 py-1 ${view === v ? "bg-indigo-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}
                  >
                    {t(v === "agenda" ? "view_agenda" : "view_calendar")}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1">
                <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(addDays(weekStart, -7))}>{t("cal_prev_week")}</button>
                <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(startOfWeek(new Date()))}>{t("cal_this_week")}</button>
                <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(addDays(weekStart, 7))}>{t("cal_next_week")}</button>
              </div>
            </div>
          }
        />
        <CardBody className="p-0">
          {loading ? (
            <div className="p-4"><LoadingState /></div>
          ) : error ? (
            <div className="p-4"><ErrorState message={error} /></div>
          ) : appts.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-400">{t(view === "agenda" ? "agenda_empty_week" : "cal_empty_week")}</div>
          ) : view === "agenda" ? (
            <WeekAgenda weekStart={weekStart} appts={appts} dayLabels={dayLabels} t={t} tStatus={tStatus} onPick={setPicked} />
          ) : (
            <WeekCalendar weekStart={weekStart} appointments={appts} dayLabels={dayLabels} onPick={setPicked} statusLabel={tStatus} />
          )}
        </CardBody>
        {appts.length > 0 && view === "calendar" && <Legend t={t} tStatus={tStatus} />}
      </Card>

      {listFilter && (
        <Modal
          onClose={() => setListFilter(null)}
          title={t(`list_title_${listFilter}`)}
        >
          <div className="space-y-2">
            {appts.filter((a) => listMatch(a, listFilter)).length === 0 ? (
              <p className="py-4 text-center text-sm text-slate-400">{t("list_empty")}</p>
            ) : (
              appts
                .filter((a) => listMatch(a, listFilter))
                .sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""))
                .map((a) => (
                  <ApptRow key={a.id} a={a} tStatus={tStatus} onClick={() => { setListFilter(null); setPicked(a); }} />
                ))
            )}
          </div>
        </Modal>
      )}

      {picked && (
        <Modal onClose={() => { setPicked(null); setActErr(null); }} title={`${picked.scheduled_at?.slice(0, 16).replace("T", " ")}`}>
          <div className="space-y-2 text-sm">
            <Row label={t("mgr_th_patient")} value={picked.patient_short ?? "-"} />
            <Row label={t("f_phone")} value={picked.phone_masked ?? "-"} />
            <Row label={t("f_service")} value={picked.service} />
            <Row label={t("f_doctor")} value={picked.doctor_name ?? "-"} />
            <div className="flex items-center gap-2">
              <StatusBadge status={picked.status} />
              <Badge tone="neutral">{tStatus(picked.source)}</Badge>
              {picked.operator_required && <Badge tone="warning">{t("mgr_op_required_mark")}</Badge>}
            </div>
          </div>

          {actErr && <p className="mt-3 text-sm text-red-600">{actErr}</p>}

          {["new", "pending", "confirmed", "operator_required"].includes(picked.status) && (
            <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-3">
              {["new", "pending", "operator_required"].includes(picked.status) && (
                <button
                  onClick={() => changeStatus(picked.id, "confirmed")}
                  disabled={acting}
                  className="rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {t("appt_confirm")}
                </button>
              )}
              {picked.status === "confirmed" && (
                <button
                  onClick={() => changeStatus(picked.id, "arrived")}
                  disabled={acting}
                  className="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {t("appt_mark_arrived")}
                </button>
              )}
              <button
                onClick={() => changeStatus(picked.id, "cancelled")}
                disabled={acting}
                className="rounded-lg border border-red-300 px-3.5 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                {t("appt_cancel_appt")}
              </button>
            </div>
          )}

          <div className="mt-3 flex justify-end border-t border-slate-100 pt-3">
            <button
              onClick={() => removeAppt(picked.id)}
              disabled={acting}
              className="text-xs text-slate-400 hover:text-red-600 disabled:opacity-50"
            >
              {t("appt_delete")}
            </button>
          </div>
        </Modal>
      )}

      {showForm && (
        <NewAppointmentForm
          doctors={doctors}
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false);
            setMessage(t("appt_created"));
            load();
          }}
        />
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 py-1.5 last:border-0">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}

function KpiButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className="rounded-lg text-left transition hover:ring-2 hover:ring-indigo-200 focus:outline-none focus:ring-2 focus:ring-indigo-300">
      {children}
    </button>
  );
}

function ApptRow({
  a,
  onClick,
  tStatus,
}: {
  a: ManagerAppointment;
  onClick: () => void;
  tStatus: (code?: string | null) => string;
}) {
  const when = a.scheduled_at?.slice(0, 16).replace("T", " ") ?? "-";
  return (
    <button
      onClick={onClick}
      className="flex w-full items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-left text-sm transition hover:border-indigo-400 hover:bg-indigo-50/40"
    >
      <div className="min-w-0">
        <div className="truncate font-medium text-slate-800">{when} · {a.patient_short ?? "-"}</div>
        <div className="truncate text-xs text-slate-500">{a.doctor_name ?? a.service}</div>
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <StatusBadge status={a.status} />
        <Badge tone="neutral">{tStatus(a.source)}</Badge>
      </div>
    </button>
  );
}

// One-tap action row used in the "needs your confirmation" feed: name + when on
// the left, large Confirm / Cancel buttons on the right. Tapping the name opens
// the full detail modal.
function ActionRow({
  a,
  t,
  acting,
  onConfirm,
  onCancel,
  onOpen,
}: {
  a: ManagerAppointment;
  t: (k: string) => string;
  acting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  onOpen: () => void;
}) {
  const when = a.scheduled_at ? a.scheduled_at.slice(0, 16).replace("T", " ") : t("rahbar_lead_no_time");
  return (
    <div className="flex flex-col gap-2.5 rounded-lg border border-slate-200 bg-white p-3 sm:flex-row sm:items-center sm:justify-between">
      <button onClick={onOpen} className="min-w-0 text-left">
        <div className="truncate font-medium text-slate-800">{a.patient_short ?? "-"}</div>
        <div className="truncate text-xs text-slate-500">{when} · {a.doctor_name ?? a.service}</div>
      </button>
      <div className="flex shrink-0 items-center gap-2">
        <button
          onClick={onConfirm}
          disabled={acting}
          className="flex-1 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 sm:flex-none"
        >
          {t("appt_confirm")}
        </button>
        <button
          onClick={onCancel}
          disabled={acting}
          className="flex-1 rounded-lg border border-red-300 px-3.5 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 sm:flex-none"
        >
          {t("appt_cancel_appt")}
        </button>
      </div>
    </div>
  );
}

function Legend({
  t,
  tStatus,
}: {
  t: (k: string) => string;
  tStatus: (code?: string | null) => string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-100 px-4 py-2.5 text-[11px] text-slate-500">
      <span className="font-medium text-slate-600">{t("cal_legend")}:</span>
      {LEGEND_STATUSES.map((s) => (
        <span key={s} className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: color(statusColor(s)) }} />
          {tStatus(s)}
        </span>
      ))}
    </div>
  );
}

// Agenda view: appointments grouped by day. Only days that actually have
// appointments are shown, so there is no wasted empty grid (mobile-friendly).
function WeekAgenda({
  weekStart,
  appts,
  dayLabels,
  t,
  tStatus,
  onPick,
}: {
  weekStart: Date;
  appts: ManagerAppointment[];
  dayLabels: string[];
  t: (k: string) => string;
  tStatus: (code?: string | null) => string;
  onPick: (a: ManagerAppointment) => void;
}) {
  const todayKey = ymd(new Date());
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const sections = days
    .map((d, i) => {
      const key = ymd(d);
      const items = appts
        .filter((a) => (a.scheduled_at ?? "").slice(0, 10) === key)
        .sort((a, b) => (a.scheduled_at ?? "").localeCompare(b.scheduled_at ?? ""));
      return { key, label: dayLabels[i], date: d, items };
    })
    .filter((s) => s.items.length > 0);

  return (
    <div className="divide-y divide-slate-100">
      {sections.map((s) => {
        const isToday = s.key === todayKey;
        return (
          <div key={s.key} className="px-4 py-3">
            <div className="mb-2 flex items-center gap-2">
              <span className={`text-sm font-semibold ${isToday ? "text-indigo-700" : "text-slate-700"}`}>
                {s.label}, {String(s.date.getDate()).padStart(2, "0")}.{String(s.date.getMonth() + 1).padStart(2, "0")}
              </span>
              {isToday && <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-medium text-indigo-700">{t("mgr_today")}</span>}
              <span className="text-xs text-slate-400">· {s.items.length} {t("appts_count")}</span>
            </div>
            <div className="space-y-2">
              {s.items.map((a) => (
                <ApptRow key={a.id} a={a} tStatus={tStatus} onClick={() => onPick(a)} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white shadow-lg" onClick={(e) => e.stopPropagation()}>
        <div className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800">{title}</div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

function NewAppointmentForm({
  doctors,
  onClose,
  onCreated,
}: {
  doctors: ManagerDoctorWorkload[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const { t } = useLanguage();
  const [service, setService] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [patient, setPatient] = useState("");
  const [phone, setPhone] = useState("");
  const [when, setWhen] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!service.trim() || !when) {
      setErr(t("appt_required_fields"));
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await createManagerAppointment({
        service: service.trim(),
        doctor_id: doctorId ? Number(doctorId) : null,
        patient_name: patient.trim() || undefined,
        patient_phone: phone.trim() || undefined,
        scheduled_at: `${when}:00Z`,
        status: "confirmed",
        source: "manual",
      });
      onCreated();
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : t("error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={t("new_appt_title")} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3 text-sm">
        <Field label={t("f_datetime")}>
          <input type="datetime-local" className="w-full rounded border px-2 py-1" value={when} onChange={(e) => setWhen(e.target.value)} required />
        </Field>
        <Field label={t("f_patient_name")}>
          <input className="w-full rounded border px-2 py-1" value={patient} onChange={(e) => setPatient(e.target.value)} />
        </Field>
        <Field label={t("f_phone")}>
          <input className="w-full rounded border px-2 py-1" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998..." />
        </Field>
        <Field label={t("f_doctor")}>
          <select className="w-full rounded border px-2 py-1" value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
            <option value="">-</option>
            {doctors.map((d) => <option key={d.doctor_id} value={String(d.doctor_id)}>{d.full_name}</option>)}
          </select>
        </Field>
        <Field label={t("f_service")}>
          <input className="w-full rounded border px-2 py-1" value={service} onChange={(e) => setService(e.target.value)} required />
        </Field>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-100">{t("f_cancel")}</button>
          <button type="submit" disabled={busy} className="rounded bg-blue-600 px-3 py-1.5 text-white disabled:opacity-50">{t("f_save")}</button>
        </div>
      </form>
    </Modal>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-slate-500">{label}</span>
      {children}
    </label>
  );
}
