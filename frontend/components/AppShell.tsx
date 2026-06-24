"use client";

import { usePathname } from "next/navigation";
import SiteHeader from "./SiteHeader";

// Each area owns its chrome; nothing bleeds across roles.
//  - /rahbar/*   -> director dashboard renders its own full-screen sidebar shell
//  - /admin/*    -> admin dashboard renders its own full-screen sidebar shell
//  - /yozilish/* -> public customer page (clean canvas, no staff nav)
//  - /login, /change-password, /  -> clean centered auth/redirect canvas
//  - anything else (e.g. /simulation) -> staff SiteHeader fallback
export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";

  if (pathname === "/" || pathname.startsWith("/rahbar") || pathname.startsWith("/admin")) {
    // Customer landing (/) and both dashboards render their own full-screen shell.
    return <>{children}</>;
  }
  if (pathname.startsWith("/yozilish")) {
    return <div className="min-h-screen bg-slate-50 px-4 py-8">{children}</div>;
  }
  if (pathname === "/login" || pathname === "/change-password") {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">{children}</div>;
  }
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </>
  );
}
