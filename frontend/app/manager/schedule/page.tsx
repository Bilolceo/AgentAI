"use client";

import { useCallback, useEffect, useState } from "react";
import { getManagerSchedule, getManagerDoctors, seedManagerDemo } from "@/lib/manager";
import { getUser } from "@/lib/auth";
import type { ManagerAppointment, ManagerDoctorWorkload } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import {
  PageHeader,
  Table,
  TH,
  TD,
  TR,
  Badge,
  StatusBadge,
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/ui";

const STATUSES = [
  "", "new", "pending", "confirmed", "arrived", "in_progress",
  "completed", "cancelled", "no_show", "operator_required",
];

function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

function fmtDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function fmtTime(s: string | null): string {
  return s ? s.replace("T", " ").slice(11, 16) : "-";
}

export default function ManagerSchedule() {
  const { t, tStatus } = useLanguage();
  const isSuper = getUser()?.role === "super_admin";
  const [view, setView] = useState<"day" | "week">("day");
  const [date, setDate] = useState<Date>(new Date());
  const [appts, setAppts] = useState<ManagerAppointment[]>([]);
  const [doctors, setDoctors] = useState<ManagerDoctorWorkload[]>([]);
  const [doctorFilter, setDoctorFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const step = view === "day" ? 1 : 7;

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params =
      view === "day"
        ? { date: fmtDate(date) }
        : { from: fmtDate(date), to: fmtDate(addDays(date, 6)) };
    getManagerSchedule(params)
      .then(setAppts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [view, date]);

  useEffect(load, [load]);
  useEffect(() => {
    getManagerDoctors().then(setDoctors).catch(() => setDoctors([]));
  }, []);

  const filtered = appts.filter(
    (a) =>
      (!doctorFilter || String(a.doctor_id) === doctorFilter) &&
      (!statusFilter || a.status === statusFilter),
  );

  async function onSeed() {
    setMessage(null);
    try {
      await seedManagerDemo();
      setMessage(t("mgr_seed_done"));
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    }
  }

  const rangeLabel = view === "day" ? fmtDate(date) : `${fmtDate(date)} - ${fmtDate(addDays(date, 6))}`;

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("mgr_sched_title")}
        actions={
          isSuper ? (
            <button onClick={onSeed} className="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-100">
              {t("mgr_seed_demo")}
            </button>
          ) : null
        }
      />
      {message && <p className="text-sm text-green-700">{message}</p>}

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <div className="inline-flex overflow-hidden rounded border border-slate-300">
          <button onClick={() => setView("day")} className={`px-3 py-1 ${view === "day" ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}>
            {t("mgr_view_day")}
          </button>
          <button onClick={() => setView("week")} className={`px-3 py-1 ${view === "week" ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}>
            {t("mgr_view_week")}
          </button>
        </div>
        <button className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100" onClick={() => setDate(addDays(date, -step))}>{t("mgr_prev")}</button>
        <button className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100" onClick={() => setDate(new Date())}>{t("mgr_today")}</button>
        <button className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-100" onClick={() => setDate(addDays(date, step))}>{t("mgr_next")}</button>
        <span className="ml-1 font-mono text-slate-700">{rangeLabel}</span>

        <select className="ml-auto rounded border px-2 py-1" value={doctorFilter} onChange={(e) => setDoctorFilter(e.target.value)}>
          <option value="">{t("mgr_all_doctors")}</option>
          {doctors.map((d) => <option key={d.doctor_id} value={String(d.doctor_id)}>{d.full_name}</option>)}
        </select>
        <select className="rounded border px-2 py-1" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUSES.map((s) => <option key={s} value={s}>{s ? tStatus(s) : t("filter_all")}</option>)}
        </select>
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : filtered.length === 0 ? (
        <EmptyState title={t("mgr_empty_day")} />
      ) : (
        <Table
          head={
            <>
              <TH>{t("mgr_th_time")}</TH>
              <TH>{t("mgr_th_patient")}</TH>
              <TH>{t("th_phone")}</TH>
              <TH>{t("mgr_th_service")}</TH>
              <TH>{t("mgr_th_doctor")}</TH>
              <TH>{t("th_status")}</TH>
              <TH>{t("mgr_th_source")}</TH>
            </>
          }
        >
          {filtered.map((a) => (
            <TR key={a.id}>
              <TD className="font-mono">{fmtTime(a.scheduled_at)}</TD>
              <TD>
                {a.patient_short ?? "-"}
                {a.operator_required && <Badge tone="warning">{t("mgr_op_required_mark")}</Badge>}
                {a.has_notes && <span className="ml-1 text-xs text-slate-400">{t("mgr_notes_mark")}</span>}
              </TD>
              <TD className="font-mono">{a.phone_masked ?? "-"}</TD>
              <TD>{a.service}</TD>
              <TD>{a.doctor_name ?? "-"}</TD>
              <TD><StatusBadge status={a.status} /></TD>
              <TD><Badge tone="neutral">{tStatus(a.source)}</Badge></TD>
            </TR>
          ))}
        </Table>
      )}
    </div>
  );
}
