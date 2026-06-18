"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCall } from "@/lib/admin";
import type { AdminCallDetail } from "@/lib/types";

export default function CallDetailPage() {
  const params = useParams<{ id: string }>();
  const [data, setData] = useState<AdminCallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCall(params.id)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!data) return null;

  return (
    <div className="space-y-5">
      <div>
        <Link href="/admin/calls" className="text-sm text-blue-600">&larr; Back to calls</Link>
        <h1 className="mt-1 text-xl font-semibold">Call #{data.id}</h1>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Field label="From" value={data.from_number} />
        <Field label="Language" value={data.language ?? "-"} />
        <Field label="Status" value={data.status} />
        <Field label="Duration" value={data.duration_seconds != null ? `${data.duration_seconds}s` : "-"} />
      </div>

      {(data.transfer || data.reason_codes.length > 0) && (
        <div className="rounded-lg border bg-amber-50 p-3 text-sm">
          {data.transfer && (
            <div>
              <span className="font-semibold">Transfer:</span> {data.transfer.reason} (priority {data.transfer.priority}, {data.transfer.status})
            </div>
          )}
          {data.reason_codes.length > 0 && (
            <div><span className="font-semibold">Safety reason codes:</span> {data.reason_codes.join(", ")}</div>
          )}
        </div>
      )}

      {data.callback && (
        <div className="rounded-lg border bg-orange-50 p-3 text-sm">
          <div className="font-semibold">Callback task #{data.callback.id}</div>
          <div>reason: {data.callback.reason} | priority: {data.callback.priority} | status: {data.callback.status}</div>
          <div>phone: {data.callback.patient_phone ?? "-"} | due: {data.callback.due_at?.replace("T", " ").slice(0, 19) ?? "-"}</div>
        </div>
      )}

      <div>
        <h2 className="mb-2 text-sm font-semibold text-gray-700">Transcript</h2>
        <div className="space-y-2">
          {data.transcripts.map((t) => (
            <div key={t.id} className={t.role === "user" ? "text-right" : "text-left"}>
              <span
                className={
                  "inline-block max-w-[80%] rounded-lg px-3 py-2 text-sm " +
                  (t.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100")
                }
              >
                <span className="mr-2 text-[10px] uppercase opacity-60">{t.role}</span>
                {t.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      {data.sources.length > 0 && (
        <div>
          <h2 className="mb-2 text-sm font-semibold text-gray-700">KB sources used</h2>
          <ul className="list-inside list-disc text-sm text-gray-600">
            {data.sources.map((s) => (
              <li key={s.id}>#{s.id} {s.title}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-white p-3">
      <div className="text-gray-800">{value}</div>
      <div className="mt-1 text-xs text-gray-500">{label}</div>
    </div>
  );
}
