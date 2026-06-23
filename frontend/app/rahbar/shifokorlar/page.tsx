"use client";

import { useEffect, useState } from "react";
import { getManagerDoctors } from "@/lib/manager";
import type { ManagerDoctorWorkload } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { PageHeader, Card, CardBody, CardHeader, Table, TH, TD, TR, Badge, LoadingState, ErrorState, EmptyState } from "@/components/ui";
import { HBars } from "@/components/charts";

export default function RahbarDoctors() {
  const { t } = useLanguage();
  const [docs, setDocs] = useState<ManagerDoctorWorkload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getManagerDoctors().then(setDocs).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  const bars = docs.map((d) => ({ label: d.full_name, value: d.appointments, sub: d.specialty ?? undefined }));

  return (
    <div className="space-y-4">
      <PageHeader title={t("mgr_doctors_title")} subtitle={t("mgr_workload_today")} />
      {docs.length === 0 ? (
        <EmptyState title={t("mgr_doctors_empty")} hint={t("mgr_gap_doctors")} />
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title={t("mgr_chart_doctors")} subtitle={t("mgr_workload_today")} />
            <CardBody><HBars items={bars} barColor="teal" /></CardBody>
          </Card>
          <Card>
            <CardHeader title={t("mgr_doctors_title")} />
            <CardBody className="p-0">
              <Table head={<><TH>{t("mgr_th_doctor")}</TH><TH>{t("mgr_th_specialty")}</TH><TH>{t("mgr_th_appointments")}</TH></>}>
                {docs.map((d) => (
                  <TR key={d.doctor_id}>
                    <TD className="font-medium">{d.full_name}</TD>
                    <TD>{d.specialty ?? "-"}</TD>
                    <TD><Badge tone={d.appointments > 0 ? "info" : "neutral"}>{d.appointments}</Badge></TD>
                  </TR>
                ))}
              </Table>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}
