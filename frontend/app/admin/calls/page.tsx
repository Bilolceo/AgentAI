"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCalls } from "@/lib/admin";
import type { AdminCall } from "@/lib/types";

const STATUSES = ["", "in_progress", "completed", "transferred"];
const LANGUAGES = ["", "uz-UZ", "ru-RU"];

export default function CallsPage() {
  const [calls, setCalls] = useState<AdminCall[]>([]);
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getCalls({ status: status || undefined, language: language || undefined })
      .then(setCalls)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [status, language]);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Call sessions</h1>

      <div className="flex gap-3 text-sm">
        <label className="flex items-center gap-1">
          Status
          <select className="rounded border px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s || "all"}</option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Language
          <select className="rounded border px-2 py-1" value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>{l || "all"}</option>
            ))}
          </select>
        </label>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : error ? (
        <p className="text-red-600">Error: {error}</p>
      ) : calls.length === 0 ? (
        <p className="text-sm text-gray-400">No calls match these filters.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">ID</th>
              <th>From</th>
              <th>Language</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Started</th>
            </tr>
          </thead>
          <tbody>
            {calls.map((c) => (
              <tr key={c.id} className="border-b hover:bg-gray-50">
                <td className="py-2">
                  <Link href={`/admin/calls/${c.id}`} className="text-blue-600">{c.id}</Link>
                </td>
                <td>{c.from_number}</td>
                <td>{c.language ?? "-"}</td>
                <td>{c.status}</td>
                <td>{c.duration_seconds != null ? `${c.duration_seconds}s` : "-"}</td>
                <td>{c.started_at?.replace("T", " ").slice(0, 19) ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
