"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  assignCallback,
  cancelCallback,
  completeCallback,
  getCallbacks,
  rescheduleCallback,
  updateCallbackNotes,
} from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { CallbackTask } from "@/lib/types";

const STATUSES = ["", "callback_required", "assigned", "completed", "cancelled"];
const PRIORITIES = ["", "urgent", "high", "normal"];
const TERMINAL = ["completed", "cancelled"];

export default function CallbacksPage() {
  const role = getUser()?.role;
  const canManage = role === "super_admin" || role === "admin";

  const [rows, setRows] = useState<CallbackTask[]>([]);
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [reason, setReason] = useState("");
  const [assignedToMe, setAssignedToMe] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    getCallbacks({
      status: status || undefined,
      priority: priority || undefined,
      reason: reason || undefined,
      assigned_to_me: assignedToMe,
    })
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [status, priority, reason, assignedToMe]); // eslint-disable-line react-hooks/exhaustive-deps

  async function act(fn: () => Promise<unknown>, ok: string) {
    setError(null);
    setMessage(null);
    try {
      await fn();
      setMessage(ok);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    }
  }

  function isOverdue(t: CallbackTask): boolean {
    return !!t.due_at && !TERMINAL.includes(t.status) && new Date(t.due_at).getTime() < Date.now();
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Callback tasks</h1>
      {message && <p className="text-sm text-green-700">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap gap-3 text-sm">
        <label className="flex items-center gap-1">
          Status
          <select className="rounded border px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "all"}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          Priority
          <select className="rounded border px-2 py-1" value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p || "all"}</option>)}
          </select>
        </label>
        <input className="rounded border px-2 py-1" placeholder="Reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={assignedToMe} onChange={(e) => setAssignedToMe(e.target.checked)} />
          assigned to me
        </label>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-gray-400">No callback tasks.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">ID</th>
              <th>Call</th>
              <th>Phone</th>
              <th>Reason</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Due</th>
              <th>Assigned</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => {
              const terminal = TERMINAL.includes(t.status);
              return (
                <tr key={t.id} className="border-b align-top hover:bg-gray-50">
                  <td className="py-2">{t.id}</td>
                  <td>
                    <Link href={`/admin/calls/${t.call_session_id}`} className="text-blue-600">#{t.call_session_id}</Link>
                  </td>
                  <td>{t.patient_phone ?? "-"}</td>
                  <td>{t.reason}</td>
                  <td>{t.priority}</td>
                  <td>{t.status}</td>
                  <td className={isOverdue(t) ? "font-medium text-red-600" : ""}>
                    {t.due_at?.replace("T", " ").slice(0, 16) ?? "-"}
                    {isOverdue(t) && " (overdue)"}
                  </td>
                  <td>{t.assigned_to_user_id ?? "-"}</td>
                  <td className="space-x-1 whitespace-nowrap">
                    {t.status === "callback_required" && (
                      <button className="rounded border px-2 py-0.5" onClick={() => act(() => assignCallback(t.id), "Assigned to you.")}>Assign to me</button>
                    )}
                    {t.status === "assigned" && (
                      <button className="rounded border px-2 py-0.5" onClick={() => act(() => completeCallback(t.id), "Completed.")}>Complete</button>
                    )}
                    {!terminal && (
                      <button
                        className="rounded border px-2 py-0.5"
                        onClick={() => {
                          const notes = window.prompt("Resolution notes:", t.resolution_notes ?? "");
                          if (notes !== null) act(() => updateCallbackNotes(t.id, notes), "Notes saved.");
                        }}
                      >
                        Notes
                      </button>
                    )}
                    {canManage && !terminal && (
                      <button
                        className="rounded border px-2 py-0.5"
                        onClick={() => {
                          const v = window.prompt("New due date/time (YYYY-MM-DDTHH:MM):", "");
                          if (v) act(() => rescheduleCallback(t.id, new Date(v).toISOString()), "Rescheduled.");
                        }}
                      >
                        Reschedule
                      </button>
                    )}
                    {canManage && !terminal && (
                      <button
                        className="rounded border border-red-300 px-2 py-0.5 text-red-700"
                        onClick={() => {
                          if (window.confirm("Cancel this callback?")) act(() => cancelCallback(t.id), "Cancelled.");
                        }}
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
