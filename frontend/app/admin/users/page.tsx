"use client";

import { useEffect, useState } from "react";
import { getUser } from "@/lib/auth";
import {
  activateUser,
  createUser,
  deactivateUser,
  listUsers,
  resetPassword,
  resetTwoFactor,
  updateUser,
} from "@/lib/users";
import type { ManagedUser, Role } from "@/lib/types";

const ROLES: Role[] = ["super_admin", "admin", "operator"];

export default function UsersPage() {
  const me = getUser();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // create form
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<Role>("operator");
  const [password, setPassword] = useState("");

  function load() {
    setLoading(true);
    listUsers()
      .then(setUsers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (me?.role === "super_admin") load();
    else setLoading(false);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (me?.role !== "super_admin") {
    return <p className="text-sm text-red-600">Forbidden: super_admin only.</p>;
  }

  async function act(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    await act(async () => {
      await createUser({ email, full_name: fullName, role, password });
      setEmail("");
      setFullName("");
      setPassword("");
      setRole("operator");
    });
  }

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold">Admin users</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <form onSubmit={onCreate} className="flex flex-wrap items-end gap-2 rounded-lg border bg-white p-3 text-sm">
        <Field label="Email"><input className="rounded border px-2 py-1" value={email} onChange={(e) => setEmail(e.target.value)} required /></Field>
        <Field label="Full name"><input className="rounded border px-2 py-1" value={fullName} onChange={(e) => setFullName(e.target.value)} /></Field>
        <Field label="Role">
          <select className="rounded border px-2 py-1" value={role} onChange={(e) => setRole(e.target.value as Role)}>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </Field>
        <Field label="Temp password"><input className="rounded border px-2 py-1" value={password} onChange={(e) => setPassword(e.target.value)} required /></Field>
        <button type="submit" className="rounded bg-blue-600 px-3 py-1.5 text-white">Create</button>
      </form>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : users.length === 0 ? (
        <p className="text-sm text-gray-400">No users.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">Email</th>
              <th>Full name</th>
              <th>Role</th>
              <th>Active</th>
              <th>2FA</th>
              <th>Last login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b align-middle hover:bg-gray-50">
                <td className="py-2">{u.email}</td>
                <td>{u.full_name ?? "-"}</td>
                <td>
                  <select
                    className="rounded border px-1 py-0.5"
                    value={u.role}
                    onChange={(e) => act(() => updateUser(u.id, { role: e.target.value as Role }))}
                  >
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </td>
                <td>{u.is_active ? "yes" : "no"}</td>
                <td>{u.two_factor_enabled ? "yes" : "no"}</td>
                <td>{u.last_login_at?.replace("T", " ").slice(0, 19) ?? "-"}</td>
                <td className="space-x-1">
                  {u.is_active ? (
                    <button className="rounded border px-2 py-0.5" onClick={() => act(() => deactivateUser(u.id))}>Deactivate</button>
                  ) : (
                    <button className="rounded border px-2 py-0.5" onClick={() => act(() => activateUser(u.id))}>Activate</button>
                  )}
                  <button
                    className="rounded border px-2 py-0.5"
                    onClick={() => {
                      const pw = window.prompt(`New temporary password for ${u.email}:`);
                      if (pw) act(() => resetPassword(u.id, pw));
                    }}
                  >
                    Reset PW
                  </button>
                  <button
                    className="rounded border px-2 py-0.5"
                    onClick={() => {
                      if (window.confirm(`Reset 2FA for ${u.email}? They must re-enroll.`)) act(() => resetTwoFactor(u.id));
                    }}
                  >
                    Reset 2FA
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-gray-500">{label}</span>
      {children}
    </label>
  );
}
