"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, loginTwoFactor } from "@/lib/auth";
import { useLanguage, LanguageSwitcher } from "@/lib/i18n";
import type { AuthUser } from "@/lib/types";

// Route each role to its home: the clinic director (manager) and read-only
// clinic staff land on /rahbar; admins/operators land on /admin.
// force_password_change always wins first.
function destinationFor(user?: AuthUser | null): string {
  if (user?.force_password_change) return "/change-password";
  if (user?.role === "manager" || user?.role === "staff") return "/rahbar";
  return "/admin";
}

export default function LoginPage() {
  const router = useRouter();
  const { t } = useLanguage();
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
        router.replace(destinationFor(outcome.user));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("login_failed"));
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
      router.replace(destinationFor(user));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("login_invalid_code"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="w-full max-w-sm">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 font-bold text-white">U</div>
          <div>
            <div className="text-sm font-semibold text-slate-900">{t("book_brand")}</div>
            <div className="text-xs text-slate-500">{t("login_title")}</div>
          </div>
        </div>
        <LanguageSwitcher />
      </div>

      {stage === "password" ? (
        <form onSubmit={onPassword} className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <Input label={t("login_email")} type="text" value={email} onChange={setEmail} />
          <Input label={t("login_password")} type="password" value={password} onChange={setPassword} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Submit busy={busy} busyLabel={t("login_please_wait")}>{t("login_signin")}</Submit>
        </form>
      ) : (
        <form onSubmit={onCode} className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-600">{t("login_2fa_hint")}</p>
          <Input label={t("login_auth_code")} type="text" value={code} onChange={setCode} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Submit busy={busy} busyLabel={t("login_please_wait")}>{t("login_verify")}</Submit>
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
      <label className="block text-sm text-slate-600">{label}</label>
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

function Submit({ busy, busyLabel, children }: { busy: boolean; busyLabel: string; children: React.ReactNode }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full rounded bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
    >
      {busy ? busyLabel : children}
    </button>
  );
}
