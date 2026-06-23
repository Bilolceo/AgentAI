"use client";

import { useEffect, useState } from "react";
import { getManagerDoctors } from "@/lib/manager";
import type { ManagerDoctorWorkload } from "@/lib/types";
import { useLanguage } from "@/lib/i18n";
import { PageHeader, Table, TH, TD, TR, Badge, LoadingState, ErrorState, EmptyState } from "@/components/ui";

export default function ManagerDoctors() {
  const { t } = useLanguage();
  const [docs, setDocs] = useState<ManagerDoctorWorkload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getManagerDoctors()
      .then(setDocs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-4">
      <PageHeader title={t("mgr_doctors_title")} subtitle={t("mgr_workload_today")} />
      {docs.length === 0 ? (
        <EmptyState title={t("mgr_doctors_empty")} hint={t("mgr_gap_doctors")} />
      ) : (
        <Table
          head={
            <>
              <TH>{t("mgr_th_doctor")}</TH>
              <TH>{t("mgr_th_specialty")}</TH>
              <TH>{t("mgr_th_appointments")}</TH>
            </>
          }
        >
          {docs.map((d) => (
            <TR key={d.doctor_id}>
              <TD className="font-medium">{d.full_name}</TD>
              <TD>{d.specialty ?? "-"}</TD>
              <TD>
                <Badge tone={d.appointments > 0 ? "info" : "neutral"}>{d.appointments}</Badge>
              </TD>
            </TR>
          ))}
        </Table>
      )}
    </div>
  );
}
