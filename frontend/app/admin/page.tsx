"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStats } from "@/lib/admin";
import type { AdminStats } from "@/lib/types";

export default function AdminOverview() {
  const [data, setData] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!data) return null;

  const cards = [
    { label: "Total calls", value: data.total_calls },
    { label: "AI resolved", value: data.ai_resolved },
    { label: "Operator transfers", value: data.operator_transfers },
    { label: "Callbacks required", value: data.callbacks_required },
    { label: "KB items", value: data.kb_items },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Overview</h1>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {cards.map((c) => (
          <div key={c.label} className="rounded-lg border bg-white p-4">
            <div className="text-2xl font-semibold">{c.value}</div>
            <div className="mt-1 text-xs text-gray-500">{c.label}</div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold text-gray-700">Recent calls</h2>
        {data.recent_calls.length === 0 ? (
          <p className="text-sm text-gray-400">No calls yet.</p>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="py-2">ID</th>
                <th>From</th>
                <th>Language</th>
                <th>Status</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_calls.map((c) => (
                <tr key={c.id} className="border-b hover:bg-gray-50">
                  <td className="py-2">
                    <Link href={`/admin/calls/${c.id}`} className="text-blue-600">
                      {c.id}
                    </Link>
                  </td>
                  <td>{c.from_number}</td>
                  <td>{c.language ?? "-"}</td>
                  <td>{c.status}</td>
                  <td>{c.started_at?.replace("T", " ").slice(0, 19) ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
