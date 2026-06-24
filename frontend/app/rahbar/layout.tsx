"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getToken, logout, me } from "@/lib/auth";
import { useLanguage, LanguageSwitcher } from "@/lib/i18n";
import { NotificationBell } from "@/components/NotificationBell";
import { IconCalendar, IconChart, IconStethoscope, IconBell, IconLogout, IconExternal } from "@/components/icons";
import type { AuthUser } from "@/lib/types";

// Director (rahbar) dashboard - a dedicated, full-screen, non-technical surface
// for the clinic owner/director. manager / admin / super_admin only.
const ALLOWED = new Set(["manager", "admin", "super_admin"]);

const NAV = [
  { href: "/rahbar", labelKey: "rahbar_nav_calendar", Icon: IconCalendar },
  { href: "/rahbar/hisobotlar", labelKey: "rahbar_nav_reports", Icon: IconChart },
  { href: "/rahbar/shifokorlar", labelKey: "rahbar_nav_doctors", Icon: IconStethoscope },
  { href: "/rahbar/bildirishnomalar", labelKey: "rahbar_nav_notifications", Icon: IconBell },
];

function initials(name: string): string {
  const p = name.trim().split(/\s+/);
  return ((p[0]?.[0] ?? "") + (p[1]?.[0] ?? "")).toUpperCase() || "R";
}

function todayLabel(): string {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.${d.getFullYear()}`;
}

export default function RahbarLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { t } = useLanguage();
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

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-500">
        {t("checking_session")}
      </div>
    );
  }
  if (!user) return null;
  if (!ALLOWED.has(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          {t("rahbar_access_denied")}
        </div>
      </div>
    );
  }

  function isActive(href: string): boolean {
    if (href === "/rahbar") return pathname === "/rahbar";
    return pathname === href || pathname.startsWith(href + "/");
  }

  const active = NAV.find((n) => isActive(n.href));
  const pageTitle = pathname === "/rahbar" ? t("rahbar_title") : t(active?.labelKey ?? "rahbar_title");

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 text-slate-900">
      {/* Sidebar */}
      <aside className="flex h-screen w-16 shrink-0 flex-col bg-slate-900 text-slate-300 md:w-64">
        <div className="flex items-center gap-3 px-3 py-5 md:px-5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-500 font-bold text-white">
            U
          </div>
          <div className="hidden md:block">
            <div className="text-sm font-semibold text-white">{t("rahbar_brand")}</div>
            <div className="text-xs text-slate-400">{t("rahbar_brand_sub")}</div>
          </div>
        </div>

        <nav className="mt-2 flex-1 space-y-1 px-2 md:px-3">
          {NAV.map(({ href, labelKey, Icon }) => {
            const on = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                title={t(labelKey)}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                  on ? "bg-slate-800 font-medium text-white" : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
                }`}
              >
                <span className={on ? "text-indigo-400" : ""}>
                  <Icon />
                </span>
                <span className="hidden md:inline">{t(labelKey)}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 p-3">
          <Link
            href="/yozilish"
            target="_blank"
            className="mb-2 flex items-center gap-3 rounded-lg px-3 py-2 text-xs text-slate-400 hover:bg-slate-800/60 hover:text-white"
            title={t("rahbar_public_link")}
          >
            <IconExternal width={16} height={16} />
            <span className="hidden md:inline">{t("rahbar_public_link")}</span>
          </Link>
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-white">
              {initials(user.full_name || user.email)}
            </div>
            <div className="hidden min-w-0 flex-1 md:block">
              <div className="truncate text-xs font-medium text-white">{user.full_name || user.email}</div>
              <button onClick={onLogout} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white">
                <IconLogout width={13} height={13} /> {t("logout")}
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-5 md:px-8">
          <div>
            <h1 className="text-base font-semibold text-slate-900 md:text-lg">{pageTitle}</h1>
            <p className="hidden text-xs text-slate-400 sm:block">{todayLabel()}</p>
          </div>
          <div className="flex items-center gap-3">
            <NotificationBell />
            <LanguageSwitcher />
          </div>
        </header>

        <main className="flex-1 overflow-auto p-5 md:p-8">{children}</main>
      </div>
    </div>
  );
}
