"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getToken, logout, me } from "@/lib/auth";
import { useLanguage, LanguageSwitcher } from "@/lib/i18n";
import {
  IconGrid, IconPhone, IconAntenna, IconActivity, IconMic, IconBook,
  IconInbox, IconClipboard, IconShield, IconUsers, IconLogout, IconMenu, IconClose,
} from "@/components/icons";
import type { AuthUser, Role } from "@/lib/types";
import type { SVGProps } from "react";

type RoleReq = "operator" | "admin" | "super_admin";
type IconCmp = (p: SVGProps<SVGSVGElement>) => JSX.Element;
type NavItem = { href: string; labelKey: string; min: RoleReq; Icon: IconCmp };
type NavGroup = { titleKey: string; items: NavItem[] };

// Grouped navigation. `min` is the lowest role allowed (rank-based below). All
// existing pages are preserved; role gating matches the backend route guards.
const GROUPS: NavGroup[] = [
  {
    titleKey: "grp_overview",
    items: [{ href: "/admin", labelKey: "nav_overview", min: "operator", Icon: IconGrid }],
  },
  {
    titleKey: "grp_calls",
    items: [
      { href: "/admin/calls", labelKey: "nav_call_history", min: "operator", Icon: IconPhone },
      { href: "/admin/telephony-calls", labelKey: "nav_telephony", min: "admin", Icon: IconAntenna },
    ],
  },
  {
    titleKey: "grp_voice",
    items: [
      { href: "/admin/provider-readiness", labelKey: "nav_readiness", min: "admin", Icon: IconActivity },
      { href: "/admin/audio-recordings", labelKey: "nav_audio", min: "admin", Icon: IconMic },
    ],
  },
  {
    titleKey: "grp_content",
    items: [{ href: "/admin/knowledge-base", labelKey: "nav_kb", min: "operator", Icon: IconBook }],
  },
  {
    titleKey: "grp_ops",
    items: [
      { href: "/admin/callbacks", labelKey: "nav_callbacks", min: "operator", Icon: IconInbox },
      { href: "/admin/audit-logs", labelKey: "nav_audit", min: "admin", Icon: IconClipboard },
    ],
  },
  {
    titleKey: "grp_security",
    items: [
      { href: "/admin/security", labelKey: "nav_security", min: "operator", Icon: IconShield },
      { href: "/admin/users", labelKey: "nav_users", min: "super_admin", Icon: IconUsers },
    ],
  },
];

const RANK: Record<RoleReq, number> = { operator: 1, admin: 2, super_admin: 3 };
function roleRank(role: Role): number {
  return RANK[role as RoleReq] ?? 0;
}

function initials(name: string): string {
  const p = name.trim().split(/\s+/);
  return ((p[0]?.[0] ?? "") + (p[1]?.[0] ?? "")).toUpperCase() || "A";
}

function todayLabel(): string {
  const d = new Date();
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.${d.getFullYear()}`;
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
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

  const rank = roleRank(user.role);
  const groups = GROUPS.map((g) => ({
    ...g,
    items: g.items.filter((i) => rank >= RANK[i.min]),
  })).filter((g) => g.items.length > 0);

  function isActive(href: string): boolean {
    if (href === "/admin") return pathname === "/admin";
    return pathname === href || pathname.startsWith(href + "/");
  }

  const activeItem = groups.flatMap((g) => g.items).find((i) => isActive(i.href));
  const pageTitle = activeItem ? t(activeItem.labelKey) : t("shell_title");

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
            <div className="truncate text-sm font-semibold text-white">{t("shell_title")}</div>
            <div className="truncate text-xs text-slate-400">{t("shell_sub")}</div>
          </div>
          <button
            onClick={() => setNavOpen(false)}
            className="-mr-1 rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
            aria-label={t("close")}
          >
            <IconClose width={20} height={20} />
          </button>
        </div>

        <nav className="mt-2 flex-1 space-y-4 overflow-y-auto px-3 pb-4">
          {groups.map((g) => (
            <div key={g.titleKey}>
              <div className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                {t(g.titleKey)}
              </div>
              <div className="space-y-1">
                {g.items.map(({ href, labelKey, Icon }) => {
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
                        <Icon width={18} height={18} />
                      </span>
                      <span>{t(labelKey)}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-800 p-3">
          <div className="flex items-center gap-3 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-semibold text-white">
              {initials(user.full_name || user.email)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-white">{user.full_name || user.email}</div>
              <div className="text-[11px] text-slate-400">{t(`role_${user.role}`)}</div>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-400 hover:bg-slate-800/60 hover:text-white"
          >
            <IconLogout width={15} height={15} />
            <span>{t("logout")}</span>
          </button>
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
          <LanguageSwitcher />
        </header>

        <main className="flex-1 overflow-auto p-4 sm:p-5 md:p-8">{children}</main>
      </div>
    </div>
  );
}
