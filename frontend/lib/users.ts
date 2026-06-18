import { authHeader } from "./auth";
import type { ManagedUser, Role } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

async function req<T>(path: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function listUsers(): Promise<ManagedUser[]> {
  return req<ManagedUser[]>("/admin/users", "GET");
}

export function createUser(payload: {
  email: string;
  full_name: string;
  role: Role;
  password: string;
}): Promise<ManagedUser> {
  return req<ManagedUser>("/admin/users", "POST", payload);
}

export function updateUser(id: number, payload: { full_name?: string; role?: Role }): Promise<ManagedUser> {
  return req<ManagedUser>(`/admin/users/${id}`, "PATCH", payload);
}

export function activateUser(id: number): Promise<ManagedUser> {
  return req<ManagedUser>(`/admin/users/${id}/activate`, "POST");
}

export function deactivateUser(id: number): Promise<ManagedUser> {
  return req<ManagedUser>(`/admin/users/${id}/deactivate`, "POST");
}

export function resetPassword(id: number, new_password: string): Promise<ManagedUser> {
  return req<ManagedUser>(`/admin/users/${id}/reset-password`, "POST", { new_password });
}

export function resetTwoFactor(id: number): Promise<ManagedUser> {
  return req<ManagedUser>(`/admin/users/${id}/reset-2fa`, "POST");
}
