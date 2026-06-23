"use client";

import { useEffect, useState } from "react";
import {
  getManagerReports,
  getManagerSchedule,
  getManagerDoctors,
  getManagerActionItems,
} from "@/lib/manager";
import type {
  ManagerReport,
  ManagerAppointment,
  ManagerDoctorWorkload,
  ManagerActionItem,
} from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import {
  PageHeader,
  SectionHeader,
  Card,
  CardBody,
  CardHeader,
  Badge,
  StatusBadge,
  SafetyBanner,
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/ui";
import { DonutChart, HBars, StatTile, statusColor, color } from "@/components/charts";

function fmtTime(s: string | null): string {
  return s ? s.replace("T", " ").slice(11, 16) : "-";
}

function todayLabel(): string {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.${d.getFullYear()}`;
}

export default function ManagerHome() {
  const { t, tStatus } = useLanguage();
  const [report, setReport] = useState<ManagerReport | null>(null);
  const [today, setToday] = useState<ManagerAppointment[]>([]);
  const [doctors, setDoctors] = useState<ManagerDoctorWorkload[]>([]);
  const [items, setItems] = useState<ManagerActionItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getManagerReports("today"),
      getManagerSchedule({}),
      getManagerDoctors(),
      getManagerActionItems(),
    ])
      .then(([rep, sched, docs, a]) => {
        setReport(rep);
        setToday(sched);
        setDoctors(docs);
        setItems(a);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const byStatus = report?.by_status ?? {};
  const total = report?.total ?? 0;
  const aiCreated = report?.ai_created ?? 0;

  const statusSegments = Object.entries(byStatus)
    .map(([s, n]) => ({ label: tStatus(s), value: n, color: statusColor(s) }))
    .sort((a, b) => b.value - a.value);
  const doctorBars = doctors
    .map((d) => ({ label: d.full_name, value: d.appointments, sub: d.specialty ?? undefined }))
    .sort((a, b) => b.value - a.value);
  const sourceSegments = [
    { label: t("mgr_source_ai"), value: aiCreated, color: "indigo" },
    { label: t("mgr_source_other"), value: Math.max(0, total - aiCreated), color: "slate" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("mgr_home_title")} subtitle={`${t("mgr_home_sub")} - ${todayLabel()}`} />

      <SafetyBanner>{t("mgr_safety")}</SafetyBanner>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatTile label={t("mgr_kpi_appt_today")} value={total} accent="blue" />
        <StatTile label={t("mgr_kpi_confirmed")} value={byStatus["confirmed"] ?? 0} accent="emerald" />
        <StatTile label={t("mgr_kpi_pending")} value={byStatus["pending"] ?? 0} accent="amber" />
        <StatTile label={t("mgr_kpi_cancelled")} value={report?.cancelled ?? 0} accent="red" />
        <StatTile label={t("mgr_kpi_op_required")} value={report?.operator_required ?? 0} accent="orange" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title={t("mgr_chart_status")} subtitle={todayLabel()} />
          <CardBody>
            {total === 0 ? (
              <EmptyState title={t("mgr_empty_today_plan")} />
            ) : (
              <DonutChart segments={statusSegments} centerValue={total} centerLabel={t("mgr_appts")} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={t("mgr_chart_doctors")} subtitle={t("mgr_workload_today")} />
          <CardBody>
            {doctorBars.length === 0 ? (
              <EmptyState title={t("mgr_doctors_empty")} />
            ) : (
              <>
                <HBars items={doctorBars} barColor="teal" />
                <div className="mt-4 border-t border-slate-100 pt-4">
                  <DonutChart
                    segments={sourceSegments}
                    size={120}
                    thickness={20}
                    centerValue={aiCreated}
                    centerLabel={t("mgr_source_ai")}
                  />
                </div>
              </>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title={t("mgr_sec_today_plan")} subtitle={t("phones_masked")} />
        <CardBody className="p-0">
          {today.length === 0 ? (
            <div className="p-4">
              <EmptyState title={t("mgr_empty_today_plan")} />
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {today.map((a) => (
                <li key={a.id} className="flex items-center gap-4 px-4 py-3">
                  <span className="w-12 shrink-0 font-mono text-sm text-slate-700">{fmtTime(a.scheduled_at)}</span>
                  <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: color(statusColor(a.status)) }} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-800">
                      {a.patient_short ?? "-"}
                      {a.operator_required && <Badge tone="warning">{t("mgr_op_required_mark")}</Badge>}
                    </div>
                    <div className="truncate text-xs text-slate-500">
                      {a.service} - {a.doctor_name ?? "-"}
                    </div>
                  </div>
                  <StatusBadge status={a.status} />
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <div>
        <SectionHeader title={t("mgr_sec_action_items")} />
        {items.length === 0 ? (
          <EmptyState title={t("mgr_empty_action")} />
        ) : (
          <div className="space-y-2">
            {items.map((it) => (
              <Card key={it.id}>
                <CardBody className="flex flex-wrap items-center gap-3">
                  <Badge tone={it.priority === "urgent" ? "danger" : it.priority === "high" ? "warning" : "neutral"}>
                    {tStatus(it.priority)}
                  </Badge>
                  <span className="text-sm text-slate-700">{tStatus(it.reason)}</span>
                  <span className="font-mono text-sm text-slate-500">{it.phone_masked ?? "-"}</span>
                  <span className="ml-auto"><StatusBadge status={it.status} /></span>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
