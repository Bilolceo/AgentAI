"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, loginTwoFactor } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [stage, setStage] = useState<"password" | "2fa">("password");
  const [ticket, setTicket] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onPassword(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const outcome = await login(email, password);
      if (outcome.twoFactorRequired) {
        setTicket(outcome.ticket!);
        setStage("2fa");
      } else {
        router.replace(outcome.user?.force_password_change ? "/change-password" : "/admin");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function onCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await loginTwoFactor(ticket, code.trim());
      router.replace(user.force_password_change ? "/change-password" : "/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid code");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">Admin login</h1>

      {stage === "password" ? (
        <form onSubmit={onPassword} className="space-y-3 rounded-lg border bg-white p-4">
          <Input label="Email" type="email" value={email} onChange={setEmail} />
          <Input label="Password" type="password" value={password} onChange={setPassword} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Submit busy={busy}>Sign in</Submit>
        </form>
      ) : (
        <form onSubmit={onCode} className="space-y-3 rounded-lg border bg-white p-4">
          <p className="text-sm text-gray-600">Enter your 6-digit code or a recovery code.</p>
          <Input label="Authentication code" type="text" value={code} onChange={setCode} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Submit busy={busy}>Verify</Submit>
        </form>
      )}
    </div>
  );
}

function Input({
  label, type, value, onChange,
}: { label: string; type: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="block text-sm text-gray-600">{label}</label>
      <input
        type={type}
        className="mt-1 w-full rounded border px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
      />
    </div>
  );
}

function Submit({ busy, children }: { busy: boolean; children: React.ReactNode }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full rounded bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
    >
      {busy ? "Please wait..." : children}
    </button>
  );
}
