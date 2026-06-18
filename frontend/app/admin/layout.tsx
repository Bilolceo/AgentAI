"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getToken, logout, me } from "@/lib/auth";
import type { AuthUser } from "@/lib/types";

const NAV = [
  { href: "/admin", label: "Overview" },
  { href: "/admin/calls", label: "Calls" },
  { href: "/admin/knowledge-base", label: "Knowledge Base" },
  { href: "/admin/callbacks", label: "Callbacks" },
  { href: "/admin/security", label: "Security (2FA)" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    me()
      .then((u) => {
        if (u.force_password_change) {
          router.replace("/change-password");
          return;
        }
        setUser(u);
      })
      .catch(() => {
        logout();
        router.replace("/login");
      })
      .finally(() => setChecking(false));
  }, [router]);

  function onLogout() {
    logout();
    router.replace("/login");
  }

  if (checking) return <p className="text-gray-500">Checking session...</p>;
  if (!user) return null;

  const nav = [...NAV];
  if (user.role === "super_admin" || user.role === "admin") {
    nav.push({ href: "/admin/telephony-calls", label: "Telephony Calls" });
    nav.push({ href: "/admin/audio-recordings", label: "Audio Recordings" });
    nav.push({ href: "/admin/audit-logs", label: "Audit Logs" });
  }
  if (user.role === "super_admin") {
    nav.push({ href: "/admin/users", label: "Users" });
  }

  return (
    <div className="flex gap-6">
      <aside className="w-48 shrink-0">
        <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-400">Admin</div>
        <nav className="flex flex-col gap-1 text-sm">
          {nav.map((n) => (
            <Link key={n.href} href={n.href} className="rounded px-2 py-1 hover:bg-gray-100">
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="mt-6 border-t pt-3 text-xs text-gray-500">
          <div className="font-medium text-gray-700">{user.full_name || user.email}</div>
          <div className="mt-0.5">{user.role}</div>
          <button onClick={onLogout} className="mt-2 rounded border px-2 py-1 hover:bg-gray-100">
            Logout
          </button>
        </div>
      </aside>
      <section className="min-w-0 flex-1">{children}</section>
    </div>
  );
}
