"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { deleteAudioRecording, getAudioRecording } from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { AudioRecordingDetail } from "@/lib/types";

function shorten(v: string, head = 10, tail = 6): string {
  if (v.length <= head + tail + 3) return v;
  return `${v.slice(0, head)}...${v.slice(-tail)}`;
}

function fmtDate(v: string | null): string {
  return v ? v.replace("T", " ").slice(0, 19) : "-";
}

export default function AudioRecordingDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const role = getUser()?.role;
  const canView = role === "super_admin" || role === "admin";

  const [data, setData] = useState<AudioRecordingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  function load() {
    if (!canView) return;
    setLoading(true);
    setError(null);
    getAudioRecording(params.id)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load recording"))
      .finally(() => setLoading(false));
  }

  useEffect(load, [params.id]); // eslint-disable-line react-hooks/exhaustive-deps

  async function onDelete() {
    if (!data || data.is_deleted) return;
    if (!window.confirm(`Soft-delete recording #${data.id}?`)) return;
    setError(null);
    setMessage(null);
    try {
      await deleteAudioRecording(data.id);
      setMessage(`Recording #${data.id} soft-deleted.`);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  if (!canView) {
    return (
      <p className="text-sm text-red-600">
        Forbidden: only super_admin and admin can view audio recordings.
      </p>
    );
  }
  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!data) return null;

  return (
    <div className="space-y-5">
      <div>
        <Link href="/admin/audio-recordings" className="text-sm text-blue-600">
          &larr; Back to audio recordings
        </Link>
        <h1 className="mt-1 text-xl font-semibold">
          Recording #{data.id} {data.is_deleted && <span className="text-sm text-red-600">(deleted)</span>}
        </h1>
      </div>

      {message && <p className="text-sm text-green-700">{message}</p>}

      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Field label="Call" value={<Link href={`/admin/calls/${data.call_session_id}`} className="text-blue-600">#{data.call_session_id}</Link>} />
        <Field label="Direction" value={data.direction} />
        <Field label="Kind" value={data.kind} />
        <Field label="Content type" value={data.content_type} />
        <Field label="Size (bytes)" value={String(data.size_bytes)} />
        <Field label="Duration (ms)" value={data.duration_ms != null ? String(data.duration_ms) : "-"} />
        <Field label="Storage provider" value={data.storage_provider} />
        <Field label="Storage key" value={shorten(data.storage_key)} />
        <Field label="Checksum (sha256)" value={shorten(data.checksum_sha256, 12, 6)} />
        <Field label="Transcript lang" value={data.transcript_language ?? "-"} />
        <Field
          label="Transcript conf."
          value={data.transcript_confidence != null ? data.transcript_confidence.toFixed(2) : "-"}
        />
        <Field label="TTS voice" value={data.tts_voice ?? "-"} />
        <Field label="Expires" value={fmtDate(data.expires_at)} />
        <Field label="Created" value={fmtDate(data.created_at)} />
        <Field label="Updated" value={fmtDate(data.updated_at)} />
      </div>

      {data.transcript_text && (
        <Block label="Transcript text" value={data.transcript_text} />
      )}
      {data.tts_text && <Block label="TTS text" value={data.tts_text} />}

      <div className="rounded border p-3 text-sm">
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Audio</div>
        {data.signed_url ? (
          <div className="space-y-2">
            <a href={data.signed_url} className="text-blue-600 underline" target="_blank" rel="noreferrer">
              Open audio URL
            </a>
            <audio controls src={data.signed_url} className="w-full" />
          </div>
        ) : (
          <p className="text-gray-500">No playable audio URL available.</p>
        )}
      </div>

      {!data.is_deleted && (
        <button
          className="rounded border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50"
          onClick={onDelete}
        >
          Soft-delete recording
        </button>
      )}
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

function Block({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border p-3 text-sm">
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">{label}</div>
      <p className="whitespace-pre-wrap break-words">{value}</p>
    </div>
  );
}
