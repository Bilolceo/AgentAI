"use client";

import { useEffect, useState } from "react";
import {
  getManagerReports,
  getManagerSchedule,
  getManagerActionItems,
  getManagerRecentCalls,
} from "@/lib/manager";
import type { ManagerReport, ManagerAppointment, ManagerActionItem, ManagerCall } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import {
  PageHeader,
  SectionHeader,
  MetricCard,
  Table,
  TH,
  TD,
  TR,
  Badge,
  StatusBadge,
  SafetyBanner,
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/ui";

function fmtTime(s: string | null): string {
  return s ? s.replace("T", " ").slice(11, 16) : "-";
}

function fmtDateTime(s: string | null): string {
  return s ? s.replace("T", " ").slice(0, 16) : "-";
}

function priorityTone(p: string): "danger" | "warning" | "neutral" {
  if (p === "urgent") return "danger";
  if (p === "high") return "warning";
  return "neutral";
}

export default function ManagerHome() {
  const { t, tStatus } = useLanguage();
  const [report, setReport] = useState<ManagerReport | null>(null);
  const [today, setToday] = useState<ManagerAppointment[]>([]);
  const [items, setItems] = useState<ManagerActionItem[]>([]);
  const [calls, setCalls] = useState<ManagerCall[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getManagerReports("today"),
      getManagerSchedule({}),
      getManagerActionItems(),
      getManagerRecentCalls(),
    ])
      .then(([rep, sched, a, c]) => {
        setReport(rep);
        setToday(sched);
        setItems(a);
        setCalls(c);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const byStatus = report?.by_status ?? {};

  return (
    <div className="space-y-6">
      <PageHeader title={t("mgr_home_title")} subtitle={t("mgr_home_sub")} />

      <SafetyBanner>{t("mgr_safety")}</SafetyBanner>

      {report ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <MetricCard label={t("mgr_kpi_appt_today")} value={report.total} />
          <MetricCard label={t("mgr_kpi_confirmed")} value={byStatus["confirmed"] ?? 0} tone="success" />
          <MetricCard label={t("mgr_kpi_pending")} value={byStatus["pending"] ?? 0} tone={(byStatus["pending"] ?? 0) > 0 ? "warning" : "neutral"} />
          <MetricCard label={t("mgr_kpi_cancelled")} value={report.cancelled} tone={report.cancelled > 0 ? "warning" : "neutral"} />
          <MetricCard label={t("mgr_kpi_op_required")} value={report.operator_required} tone={report.operator_required > 0 ? "danger" : "neutral"} />
        </div>
      ) : null}

      {/* Today's plan timeline (real appointments). */}
      <div>
        <SectionHeader title={t("mgr_sec_today_plan")} hint={t("phones_masked")} />
        {today.length === 0 ? (
          <EmptyState title={t("mgr_empty_today_plan")} />
        ) : (
          <Table
            head={
              <>
                <TH>{t("mgr_th_time")}</TH>
                <TH>{t("mgr_th_patient")}</TH>
                <TH>{t("mgr_th_service")}</TH>
                <TH>{t("mgr_th_doctor")}</TH>
                <TH>{t("th_status")}</TH>
              </>
            }
          >
            {today.map((a) => (
              <TR key={a.id}>
                <TD className="font-mono">{fmtTime(a.scheduled_at)}</TD>
                <TD>
                  {a.patient_short ?? "-"}
                  {a.operator_required && <Badge tone="warning">{t("mgr_op_required_mark")}</Badge>}
                </TD>
                <TD>{a.service}</TD>
                <TD>{a.doctor_name ?? "-"}</TD>
                <TD><StatusBadge status={a.status} /></TD>
              </TR>
            ))}
          </Table>
        )}
      </div>

      {/* Action items needing attention (real callbacks). */}
      <div>
        <SectionHeader title={t("mgr_sec_action_items")} />
        {items.length === 0 ? (
          <EmptyState title={t("mgr_empty_action")} />
        ) : (
          <Table
            head={
              <>
                <TH>{t("th_reason")}</TH>
                <TH>{t("th_priority")}</TH>
                <TH>{t("th_status")}</TH>
                <TH>{t("th_phone")}</TH>
                <TH>{t("th_due")}</TH>
              </>
            }
          >
            {items.map((it) => (
              <TR key={it.id}>
                <TD>{tStatus(it.reason)}</TD>
                <TD><Badge tone={priorityTone(it.priority)}>{tStatus(it.priority)}</Badge></TD>
                <TD><StatusBadge status={it.status} /></TD>
                <TD className="font-mono">{it.phone_masked ?? "-"}</TD>
                <TD className="text-slate-500">{fmtDateTime(it.due_at)}</TD>
              </TR>
            ))}
          </Table>
        )}
      </div>

      {/* Recent calls (masked). */}
      <div>
        <SectionHeader title={t("mgr_sec_recent_calls")} />
        {calls.length === 0 ? (
          <EmptyState title={t("mgr_empty_calls")} />
        ) : (
          <Table
            head={
              <>
                <TH>{t("th_from")}</TH>
                <TH>{t("th_language")}</TH>
                <TH>{t("th_status")}</TH>
                <TH>{t("th_started")}</TH>
              </>
            }
          >
            {calls.map((c) => (
              <TR key={c.id}>
                <TD className="font-mono">{c.from_masked ?? "-"}</TD>
                <TD>{c.language ?? "-"}</TD>
                <TD><StatusBadge status={c.status} /></TD>
                <TD className="text-slate-500">{fmtDateTime(c.started_at)}</TD>
              </TR>
            ))}
          </Table>
        )}
      </div>
    </div>
  );
}
