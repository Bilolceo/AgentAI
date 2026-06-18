"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { changePassword, getToken, logout } from "@/lib/auth";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await changePassword(oldPassword, newPassword);
      // Token was invalidated by the version bump; require a fresh login.
      logout();
      router.replace("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-2 text-xl font-semibold">Change password</h1>
      <p className="mb-4 text-sm text-gray-600">
        You must set a new password before continuing. Minimum 10 characters with a letter and a digit.
      </p>
      <form onSubmit={onSubmit} className="space-y-3 rounded-lg border bg-white p-4">
        <div>
          <label className="block text-sm text-gray-600">Current password</label>
          <input type="password" className="mt-1 w-full rounded border px-3 py-2 text-sm" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
        </div>
        <div>
          <label className="block text-sm text-gray-600">New password</label>
          <input type="password" className="mt-1 w-full rounded border px-3 py-2 text-sm" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={busy} className="w-full rounded bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50">
          {busy ? "Saving..." : "Change password"}
        </button>
      </form>
    </div>
  );
}
