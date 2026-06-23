"use client";

import { useEffect, useState } from "react";
import { getManagerReports } from "@/lib/manager";
import type { ManagerReport } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { PageHeader, Card, CardBody, CardHeader, LoadingState, ErrorState, EmptyState } from "@/components/ui";
import { DonutChart, HBars, StatTile, statusColor } from "@/components/charts";

const RANGES = [
  { key: "today", labelKey: "mgr_range_today" },
  { key: "week", labelKey: "mgr_range_week" },
  { key: "month", labelKey: "mgr_range_month" },
];

export default function RahbarReports() {
  const { t, tStatus } = useLanguage();
  const [range, setRange] = useState("week");
  const [rep, setRep] = useState<ManagerReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getManagerReports(range).then(setRep).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [range]);

  const statusSegments = Object.entries(rep?.by_status ?? {})
    .map(([s, n]) => ({ label: tStatus(s), value: n, color: statusColor(s) }))
    .sort((a, b) => b.value - a.value);
  const doctorBars = (rep?.by_doctor ?? [])
    .map((d) => ({ label: d.full_name, value: d.appointments, sub: d.specialty ?? undefined }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="space-y-5">
      <PageHeader
        title={t("mgr_reports_title")}
        actions={
          <div className="inline-flex overflow-hidden rounded border border-slate-300 text-sm">
            {RANGES.map((r) => (
              <button key={r.key} onClick={() => setRange(r.key)} className={`px-3 py-1 ${range === r.key ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}>
                {t(r.labelKey)}
              </button>
            ))}
          </div>
        }
      />
      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> : !rep ? null : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <StatTile label={t("mgr_rep_total")} value={rep.total} accent="blue" />
            <StatTile label={t("mgr_rep_ai_created")} value={rep.ai_created} accent="indigo" />
            <StatTile label={t("mgr_rep_op_required")} value={rep.operator_required} accent="orange" />
            <StatTile label={t("mgr_rep_cancelled")} value={rep.cancelled} accent="red" />
            <StatTile label={t("mgr_rep_no_show")} value={rep.no_show} accent="rose" />
          </div>
          {rep.total === 0 ? (
            <EmptyState title={t("mgr_rep_empty")} />
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader title={t("mgr_rep_by_status")} />
                <CardBody><DonutChart segments={statusSegments} centerValue={rep.total} centerLabel={t("mgr_appts")} /></CardBody>
              </Card>
              <Card>
                <CardHeader title={t("mgr_rep_by_doctor")} />
                <CardBody>
                  {doctorBars.length === 0 ? <EmptyState title={t("mgr_doctors_empty")} /> : <HBars items={doctorBars} barColor="teal" />}
                </CardBody>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}
