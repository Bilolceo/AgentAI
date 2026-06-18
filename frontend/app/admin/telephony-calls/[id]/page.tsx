"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getTelephonyCall } from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { TelephonyCall } from "@/lib/types";

function fmtDate(v: string | null): string {
  return v ? v.replace("T", " ").slice(0, 19) : "-";
}

export default function TelephonyCallDetailPage() {
  const params = useParams<{ id: string }>();
  const role = getUser()?.role;
  const canView = role === "super_admin" || role === "admin";

  const [data, setData] = useState<TelephonyCall | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    getTelephonyCall(params.id)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load telephony call"))
      .finally(() => setLoading(false));
  }, [params.id, canView]);

  if (!canView) {
    return (
      <p className="text-sm text-red-600">
        Forbidden: only super_admin and admin can view telephony calls.
      </p>
    );
  }
  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!data) return null;

  return (
    <div className="space-y-5">
      <div>
        <Link href="/admin/telephony-calls" className="text-sm text-blue-600">
          &larr; Back to telephony calls
        </Link>
        <h1 className="mt-1 text-xl font-semibold">Telephony call #{data.id}</h1>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Field label="Provider" value={data.provider} />
        <Field label="Provider call ID" value={data.provider_call_id ?? "-"} />
        <Field label="Status" value={data.status} />
        <Field label="Direction" value={data.direction} />
        <Field label="From" value={data.from_number ?? "-"} />
        <Field label="To" value={data.to_number ?? "-"} />
        <Field
          label="Call session"
          value={
            data.call_session_id != null ? (
              <Link href={`/admin/calls/${data.call_session_id}`} className="text-blue-600">
                #{data.call_session_id}
              </Link>
            ) : "-"
          }
        />
        <Field label="Started" value={fmtDate(data.started_at)} />
        <Field label="Ended" value={fmtDate(data.ended_at)} />
        <Field label="Created" value={fmtDate(data.created_at)} />
        <Field label="Updated" value={fmtDate(data.updated_at)} />
      </div>

      {data.call_session_id != null && (
        <div className="flex flex-wrap gap-3 text-sm">
          <Link
            href={`/admin/calls/${data.call_session_id}`}
            className="rounded border px-3 py-1 text-blue-600 hover:bg-gray-50"
          >
            View call detail
          </Link>
          <Link
            href={`/admin/audio-recordings?call_id=${data.call_session_id}`}
            className="rounded border px-3 py-1 text-blue-600 hover:bg-gray-50"
          >
            View audio recordings
          </Link>
        </div>
      )}

      <details className="rounded border p-3 text-sm" open>
        <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-gray-400">
          Safe raw metadata
        </summary>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-xs text-gray-700">
          {data.raw_metadata ? JSON.stringify(data.raw_metadata, null, 2) : "(none)"}
        </pre>
      </details>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-gray-400">{label}</div>
      <div className="mt-0.5 break-all">{value}</div>
    </div>
  );
}
