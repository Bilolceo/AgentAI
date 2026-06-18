import type { AuthUser } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";
const TOKEN_KEY = "cc_token";
const USER_KEY = "cc_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as AuthUser) : null;
}

export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function store(token: string, user: AuthUser): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export interface LoginOutcome {
  twoFactorRequired: boolean;
  ticket?: string;
  user?: AuthUser;
}

export async function login(email: string, password: string): Promise<LoginOutcome> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    if (res.status === 423) throw new Error("Account temporarily locked. Try again later.");
    throw new Error(res.status === 401 ? "Invalid credentials or inactive user" : `Login failed: ${res.status}`);
  }
  const data = await res.json();
  if (data.two_factor_required) {
    return { twoFactorRequired: true, ticket: data.two_factor_ticket as string };
  }
  store(data.access_token, data.user);
  return { twoFactorRequired: false, user: data.user as AuthUser };
}

export async function loginTwoFactor(ticket: string, code: string): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/login/2fa`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${ticket}` },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    if (res.status === 423) throw new Error("Account temporarily locked. Try again later.");
    throw new Error(res.status === 401 ? "Invalid 2FA code" : `Failed: ${res.status}`);
  }
  const data = await res.json();
  store(data.access_token, data.user);
  return data.user as AuthUser;
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Failed: ${res.status}`);
  }
}

export async function me(): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeader(), cache: "no-store" });
  if (!res.ok) throw new Error(`Unauthorized: ${res.status}`);
  const user: AuthUser = await res.json();
  if (typeof window !== "undefined") window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  return user;
}

export function logout(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

// --- 2FA management (requires an access token) ------------------------------
async function post2fa<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function enroll2fa(): Promise<{ secret: string; otpauth_uri: string }> {
  return post2fa("/auth/2fa/enroll");
}

export function confirm2fa(code: string): Promise<{ recovery_codes: string[] }> {
  return post2fa("/auth/2fa/confirm", { code });
}

export function disable2fa(code: string): Promise<{ two_factor_enabled: boolean }> {
  return post2fa("/auth/2fa/disable", { code });
}

export function regenerateRecoveryCodes(code: string): Promise<{ recovery_codes: string[] }> {
  return post2fa("/auth/2fa/recovery-codes/regenerate", { code });
}
