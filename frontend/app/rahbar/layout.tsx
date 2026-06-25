"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getToken, logout, me } from "@/lib/auth";
import { useLanguage, LanguageSwitcher } from "@/lib/i18n";
import { NotificationBell } from "@/components/NotificationBell";
import { IconCalendar, IconChart, IconStethoscope, IconBell, IconLogout, IconExternal, IconMenu, IconClose } from "@/components/icons";
import type { AuthUser } from "@/lib/types";

// Director (rahbar) dashboard - a dedicated, full-screen, non-technical surface
// for the clinic owner/director. Read-only clinic staff also land here but
// without any confirm/cancel/create controls (gated in the pages themselves).
const ALLOWED = new Set(["manager", "admin", "super_admin", "staff"]);

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
  const [navOpen, setNavOpen] = useState(false);

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

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
  const homeTitle = user.role === "staff" ? "staff_title" : "rahbar_title";
  const pageTitle = pathname === "/rahbar" ? t(homeTitle) : t(active?.labelKey ?? homeTitle);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100 text-slate-900">
      {/* Mobile drawer backdrop */}
      {navOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={() => setNavOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar — off-canvas drawer on mobile, static rail on md+ */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex h-screen w-64 shrink-0 flex-col bg-slate-900 text-slate-300 transition-transform duration-200 md:static md:z-auto md:translate-x-0 md:shadow-none ${
          navOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 px-5 py-5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-500 font-bold text-white">
            U
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold text-white">{t(user.role === "staff" ? "staff_brand" : "rahbar_brand")}</div>
            <div className="truncate text-xs text-slate-400">{t(user.role === "staff" ? "staff_brand_sub" : "rahbar_brand_sub")}</div>
          </div>
          <button
            onClick={() => setNavOpen(false)}
            className="-mr-1 rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
            aria-label={t("close")}
          >
            <IconClose width={20} height={20} />
          </button>
        </div>

        <nav className="mt-2 flex-1 space-y-1 px-3">
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
                <span>{t(labelKey)}</span>
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
            <span>{t("rahbar_public_link")}</span>
          </Link>
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-white">
              {initials(user.full_name || user.email)}
            </div>
            <div className="min-w-0 flex-1">
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
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-slate-200 bg-white px-4 md:px-8">
          <button
            onClick={() => setNavOpen(true)}
            className="-ml-1 rounded-lg p-1.5 text-slate-600 hover:bg-slate-100 md:hidden"
            aria-label={t("menu_open")}
          >
            <IconMenu width={22} height={22} />
          </button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-base font-semibold text-slate-900 md:text-lg">{pageTitle}</h1>
            <p className="hidden text-xs text-slate-400 sm:block">{todayLabel()}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <NotificationBell />
            <LanguageSwitcher />
          </div>
        </header>

        <main className="flex-1 overflow-auto p-4 sm:p-5 md:p-8">{children}</main>
      </div>
    </div>
  );
}
