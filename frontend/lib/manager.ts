import { authHeader } from "./auth";
import type {
  ManagerActionItem,
  ManagerAppointment,
  ManagerCall,
  ManagerDoctorWorkload,
  ManagerReport,
  ManagerStats,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store", headers: authHeader() });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function postJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { ...authHeader(), "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

async function patchJSON<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { ...authHeader(), "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export function setManagerAppointmentStatus(id: number, status: string): Promise<ManagerAppointment> {
  return patchJSON<ManagerAppointment>(`/manager/appointments/${id}/status`, { status });
}

export interface NewAppointmentInput {
  service: string;
  doctor_id?: number | null;
  patient_name?: string;
  patient_phone?: string;
  scheduled_at?: string;
  status?: string;
  source?: string;
}

export function createManagerAppointment(payload: NewAppointmentInput): Promise<ManagerAppointment> {
  return postJSON<ManagerAppointment>("/manager/appointments", payload);
}

export function getManagerStats(): Promise<ManagerStats> {
  return getJSON<ManagerStats>("/manager/stats");
}

export function getManagerActionItems(): Promise<ManagerActionItem[]> {
  return getJSON<ManagerActionItem[]>("/manager/action-items");
}

export function getManagerRecentCalls(): Promise<ManagerCall[]> {
  return getJSON<ManagerCall[]>("/manager/recent-calls");
}

export function getManagerSchedule(
  params: { date?: string; from?: string; to?: string } = {},
): Promise<ManagerAppointment[]> {
  const q = new URLSearchParams();
  if (params.date) q.set("date", params.date);
  if (params.from) q.set("from", params.from);
  if (params.to) q.set("to", params.to);
  const qs = q.toString();
  return getJSON<ManagerAppointment[]>(`/manager/schedule${qs ? `?${qs}` : ""}`);
}

export function getManagerDoctors(): Promise<ManagerDoctorWorkload[]> {
  return getJSON<ManagerDoctorWorkload[]>("/manager/doctors");
}

export function getManagerReports(range: string): Promise<ManagerReport> {
  return getJSON<ManagerReport>(`/manager/reports?range=${encodeURIComponent(range)}`);
}

export function seedManagerDemo(): Promise<{ seeded: boolean }> {
  return postJSON<{ seeded: boolean }>("/manager/seed-demo");
}
