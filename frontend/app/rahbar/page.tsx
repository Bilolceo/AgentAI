"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getManagerSchedule,
  getManagerDoctors,
  getManagerReports,
  createManagerAppointment,
  setManagerAppointmentStatus,
} from "@/lib/manager";
import type { ManagerAppointment, ManagerDoctorWorkload, ManagerReport } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { Card, CardBody, CardHeader, StatusBadge, Badge, LoadingState, ErrorState } from "@/components/ui";
import { StatTile } from "@/components/charts";
import { WeekCalendar, startOfWeek, addDays, ymd } from "@/components/calendar";
import { IconPlus } from "@/components/icons";

export default function RahbarHome() {
  const { t, tStatus } = useLanguage();
  const [weekStart, setWeekStart] = useState<Date>(startOfWeek(new Date()));
  const [appts, setAppts] = useState<ManagerAppointment[]>([]);
  const [doctors, setDoctors] = useState<ManagerDoctorWorkload[]>([]);
  const [report, setReport] = useState<ManagerReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [picked, setPicked] = useState<ManagerAppointment | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [acting, setActing] = useState(false);
  const [actErr, setActErr] = useState<string | null>(null);

  const refreshToday = useCallback(() => {
    getManagerReports("today").then(setReport).catch(() => setReport(null));
  }, []);

  async function changeStatus(id: number, status: string) {
    setActing(true);
    setActErr(null);
    try {
      const updated = await setManagerAppointmentStatus(id, status);
      setPicked(updated);
      setMessage(t("appt_status_updated"));
      load();
      refreshToday();
    } catch (e) {
      setActErr(e instanceof Error ? e.message : t("error"));
    } finally {
      setActing(false);
    }
  }

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getManagerSchedule({ from: ymd(weekStart), to: ymd(addDays(weekStart, 6)) })
      .then(setAppts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [weekStart]);

  useEffect(load, [load]);
  useEffect(() => {
    getManagerDoctors().then(setDoctors).catch(() => setDoctors([]));
    getManagerReports("today").then(setReport).catch(() => setReport(null));
  }, []);

  const dayLabels = [
    t("dow_mon"), t("dow_tue"), t("dow_wed"), t("dow_thu"), t("dow_fri"), t("dow_sat"), t("dow_sun"),
  ];
  const weekRange = `${ymd(weekStart)} - ${ymd(addDays(weekStart, 6))}`;
  const byStatus = report?.by_status ?? {};

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

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile label={t("kpi_today_appts")} value={report?.total ?? 0} accent="blue" />
        <StatTile label={t("kpi_week_appts")} value={appts.length} accent="indigo" />
        <StatTile label={t("mgr_kpi_confirmed")} value={byStatus["confirmed"] ?? 0} accent="emerald" />
        <StatTile label={t("mgr_kpi_cancelled")} value={report?.cancelled ?? 0} accent="red" />
      </div>

      <Card>
        <CardHeader
          title={t("rahbar_nav_calendar")}
          subtitle={weekRange}
          actions={
            <div className="flex items-center gap-1">
              <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(addDays(weekStart, -7))}>{t("cal_prev_week")}</button>
              <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(startOfWeek(new Date()))}>{t("cal_this_week")}</button>
              <button className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100" onClick={() => setWeekStart(addDays(weekStart, 7))}>{t("cal_next_week")}</button>
            </div>
          }
        />
        <CardBody className="p-0">
          {loading ? (
            <div className="p-4"><LoadingState /></div>
          ) : error ? (
            <div className="p-4"><ErrorState message={error} /></div>
          ) : appts.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-400">{t("cal_empty_week")}</div>
          ) : (
            <WeekCalendar weekStart={weekStart} appointments={appts} dayLabels={dayLabels} onPick={setPicked} />
          )}
        </CardBody>
      </Card>

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
