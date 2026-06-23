"use client";

import { useEffect, useState } from "react";
import { getManagerReports } from "@/lib/manager";
import type { ManagerReport } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import {
  PageHeader,
  MetricCard,
  Card,
  CardBody,
  CardHeader,
  Table,
  TH,
  TD,
  TR,
  Badge,
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/ui";

const RANGES: { key: string; labelKey: string }[] = [
  { key: "today", labelKey: "mgr_range_today" },
  { key: "week", labelKey: "mgr_range_week" },
  { key: "month", labelKey: "mgr_range_month" },
];

export default function ManagerReports() {
  const { t, tStatus } = useLanguage();
  const [range, setRange] = useState("today");
  const [rep, setRep] = useState<ManagerReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getManagerReports(range)
      .then(setRep)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [range]);

  return (
    <div className="space-y-5">
      <PageHeader
        title={t("mgr_reports_title")}
        actions={
          <div className="inline-flex overflow-hidden rounded border border-slate-300 text-sm">
            {RANGES.map((r) => (
              <button
                key={r.key}
                onClick={() => setRange(r.key)}
                className={`px-3 py-1 ${range === r.key ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"}`}
              >
                {t(r.labelKey)}
              </button>
            ))}
          </div>
        }
      />

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : !rep ? null : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard label={t("mgr_rep_total")} value={rep.total} />
            <MetricCard label={t("mgr_rep_ai_created")} value={rep.ai_created} tone="info" />
            <MetricCard label={t("mgr_rep_op_required")} value={rep.operator_required} tone={rep.operator_required > 0 ? "warning" : "neutral"} />
            <MetricCard label={t("mgr_rep_cancelled")} value={rep.cancelled} tone={rep.cancelled > 0 ? "warning" : "neutral"} />
            <MetricCard label={t("mgr_rep_no_show")} value={rep.no_show} tone={rep.no_show > 0 ? "danger" : "neutral"} />
          </div>

          {rep.total === 0 ? (
            <EmptyState title={t("mgr_rep_empty")} />
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader title={t("mgr_rep_by_status")} />
                <CardBody>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(rep.by_status).map(([s, n]) => (
                      <Badge key={s} tone="neutral">{tStatus(s)}: {n}</Badge>
                    ))}
                  </div>
                </CardBody>
              </Card>

              <Card>
                <CardHeader title={t("mgr_rep_by_doctor")} />
                <CardBody className="p-0">
                  <Table
                    head={
                      <>
                        <TH>{t("mgr_th_doctor")}</TH>
                        <TH>{t("mgr_th_appointments")}</TH>
                      </>
                    }
                  >
                    {rep.by_doctor.map((d) => (
                      <TR key={d.doctor_id}>
                        <TD>{d.full_name}</TD>
                        <TD><Badge tone="info">{d.appointments}</Badge></TD>
                      </TR>
                    ))}
                  </Table>
                </CardBody>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}
