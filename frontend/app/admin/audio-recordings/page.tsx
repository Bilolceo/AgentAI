"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { deleteAudioRecording, getAudioRecordings } from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { AudioRecording } from "@/lib/types";

const DIRECTIONS = ["", "inbound", "outbound"];
const KINDS = ["", "user_audio", "ai_tts", "full_call", "system"];
const PAGE_SIZE = 25;

function fmtDate(v: string | null): string {
  return v ? v.replace("T", " ").slice(0, 19) : "-";
}

export default function AudioRecordingsPage() {
  const role = getUser()?.role;
  const canView = role === "super_admin" || role === "admin";

  const [rows, setRows] = useState<AudioRecording[]>([]);
  const [callId, setCallId] = useState("");

  // Pre-fill the call_id filter when linked from another page (?call_id=...).
  useEffect(() => {
    if (typeof window === "undefined") return;
    const fromUrl = new URLSearchParams(window.location.search).get("call_id");
    if (fromUrl && /^[0-9]+$/.test(fromUrl)) setCallId(fromUrl);
  }, []);

  const [direction, setDirection] = useState("");
  const [kind, setKind] = useState("");
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  function load() {
    if (!canView) return;
    setLoading(true);
    setError(null);
    const callIdNum = callId.trim() === "" ? undefined : Number(callId);
    getAudioRecordings({
      call_id: Number.isFinite(callIdNum) ? callIdNum : undefined,
      direction: direction || undefined,
      kind: kind || undefined,
      include_deleted: includeDeleted,
      limit: PAGE_SIZE,
      offset,
    })
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load recordings"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [callId, direction, kind, includeDeleted, offset]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reset to first page whenever a filter changes.
  useEffect(() => setOffset(0), [callId, direction, kind, includeDeleted]);

  async function onDelete(rec: AudioRecording) {
    if (!window.confirm(`Soft-delete recording #${rec.id}? This hides it from the default list.`)) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await deleteAudioRecording(rec.id);
      setMessage(`Recording #${rec.id} soft-deleted.`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  if (!canView) {
    return (
      <div className="space-y-2">
        <h1 className="text-xl font-semibold">Audio recordings</h1>
        <p className="text-sm text-red-600">
          Forbidden: only super_admin and admin can view audio recordings.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Audio recordings</h1>
      <p className="text-xs text-gray-400">
        Metadata only. Raw audio bytes are never exposed here.
      </p>
      {message && <p className="text-sm text-green-700">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <input
          className="w-28 rounded border px-2 py-1"
          placeholder="Call ID"
          inputMode="numeric"
          value={callId}
          onChange={(e) => setCallId(e.target.value.replace(/[^0-9]/g, ""))}
        />
        <label className="flex items-center gap-1">
          Direction
          <select className="rounded border px-2 py-1" value={direction} onChange={(e) => setDirection(e.target.value)}>
            {DIRECTIONS.map((d) => <option key={d} value={d}>{d || "all"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Kind
          <select className="rounded border px-2 py-1" value={kind} onChange={(e) => setKind(e.target.value)}>
            {KINDS.map((k) => <option key={k} value={k}>{k || "all"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.target.checked)} />
          include deleted
        </label>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">No audio recordings match these filters.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">ID</th>
              <th>Call</th>
              <th>Direction</th>
              <th>Kind</th>
              <th>Content type</th>
              <th>Size</th>
              <th>Duration</th>
              <th>Lang</th>
              <th>Conf.</th>
              <th>Voice</th>
              <th>Expires</th>
              <th>Created</th>
              <th>Deleted</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b align-top hover:bg-gray-50">
                <td className="py-2">
                  <Link href={`/admin/audio-recordings/${r.id}`} className="text-blue-600">#{r.id}</Link>
                </td>
                <td>
                  <Link href={`/admin/calls/${r.call_session_id}`} className="text-blue-600">#{r.call_session_id}</Link>
                </td>
                <td>{r.direction}</td>
                <td>{r.kind}</td>
                <td>{r.content_type}</td>
                <td>{r.size_bytes}</td>
                <td>{r.duration_ms ?? "-"}</td>
                <td>{r.transcript_language ?? "-"}</td>
                <td>{r.transcript_confidence != null ? r.transcript_confidence.toFixed(2) : "-"}</td>
                <td>{r.tts_voice ?? "-"}</td>
                <td>{fmtDate(r.expires_at)}</td>
                <td>{fmtDate(r.created_at)}</td>
                <td>{r.is_deleted ? "yes" : "no"}</td>
                <td className="whitespace-nowrap">
                  {!r.is_deleted && (
                    <button
                      className="rounded border border-red-300 px-2 py-0.5 text-red-700"
                      onClick={() => onDelete(r)}
                    >
                      Delete
                    </button>
                  )}
                </td>
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
