"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTelephonyCalls } from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { TelephonyCall } from "@/lib/types";

const PROVIDERS = ["", "mock", "twilio"];
const STATUSES = ["", "received", "processed", "failed"];
const DIRECTIONS = ["", "inbound", "outbound"];
const PAGE_SIZE = 25;

function fmtDate(v: string | null): string {
  return v ? v.replace("T", " ").slice(0, 19) : "-";
}

// Mask middle digits of a phone number for the list view.
function maskNumber(v: string | null): string {
  if (!v) return "-";
  if (v.length <= 5) return v;
  return `${v.slice(0, 4)}***${v.slice(-2)}`;
}

export default function TelephonyCallsPage() {
  const role = getUser()?.role;
  const canView = role === "super_admin" || role === "admin";

  const [rows, setRows] = useState<TelephonyCall[]>([]);
  const [provider, setProvider] = useState("");
  const [status, setStatus] = useState("");
  const [direction, setDirection] = useState("");
  const [callSessionId, setCallSessionId] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!canView) return;
    setLoading(true);
    setError(null);
    const csid = callSessionId.trim() === "" ? undefined : Number(callSessionId);
    getTelephonyCalls({
      provider: provider || undefined,
      status: status || undefined,
      direction: direction || undefined,
      call_session_id: Number.isFinite(csid) ? csid : undefined,
      limit: PAGE_SIZE,
      offset,
    })
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load telephony calls"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [provider, status, direction, callSessionId, offset]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => setOffset(0), [provider, status, direction, callSessionId]);

  if (!canView) {
    return (
      <div className="space-y-2">
        <h1 className="text-xl font-semibold">Telephony calls</h1>
        <p className="text-sm text-red-600">
          Forbidden: only super_admin and admin can view telephony calls.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Telephony calls</h1>
      <p className="text-xs text-gray-400">
        Intake metadata from the mock telephony webhook. Secrets are never exposed.
      </p>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label className="flex items-center gap-1">
          Provider
          <select className="rounded border px-2 py-1" value={provider} onChange={(e) => setProvider(e.target.value)}>
            {PROVIDERS.map((p) => <option key={p} value={p}>{p || "all"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Status
          <select className="rounded border px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "all"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Direction
          <select className="rounded border px-2 py-1" value={direction} onChange={(e) => setDirection(e.target.value)}>
            {DIRECTIONS.map((d) => <option key={d} value={d}>{d || "all"}</option>)}
          </select>
        </label>
        <input
          className="w-32 rounded border px-2 py-1"
          placeholder="Call session ID"
          inputMode="numeric"
          value={callSessionId}
          onChange={(e) => setCallSessionId(e.target.value.replace(/[^0-9]/g, ""))}
        />
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">No telephony calls match these filters.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">ID</th>
              <th>Provider</th>
              <th>Provider call ID</th>
              <th>Status</th>
              <th>Direction</th>
              <th>From</th>
              <th>To</th>
              <th>Call</th>
              <th>Started</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b align-top hover:bg-gray-50">
                <td className="py-2">
                  <Link href={`/admin/telephony-calls/${r.id}`} className="text-blue-600">#{r.id}</Link>
                </td>
                <td>{r.provider}</td>
                <td>{r.provider_call_id ?? "-"}</td>
                <td>{r.status}</td>
                <td>{r.direction}</td>
                <td>{maskNumber(r.from_number)}</td>
                <td>{maskNumber(r.to_number)}</td>
                <td>
                  {r.call_session_id != null ? (
                    <Link href={`/admin/calls/${r.call_session_id}`} className="text-blue-600">#{r.call_session_id}</Link>
                  ) : "-"}
                </td>
                <td>{fmtDate(r.started_at)}</td>
                <td>{fmtDate(r.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="flex items-center gap-3 text-sm">
        <button
          className="rounded border px-2 py-1 disabled:opacity-40"
          disabled={offset === 0 || loading}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          Prev
        </button>
        <span className="text-gray-500">
          rows {rows.length === 0 ? 0 : offset + 1}-{offset + rows.length}
        </span>
        <button
          className="rounded border px-2 py-1 disabled:opacity-40"
          disabled={rows.length < PAGE_SIZE || loading}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
