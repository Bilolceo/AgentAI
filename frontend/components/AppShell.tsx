"use client";

import { usePathname } from "next/navigation";
import SiteHeader from "./SiteHeader";

// Chooses the chrome per route:
//  - /rahbar/*   -> full-bleed; the rahbar layout renders its own dashboard shell
//  - /yozilish/* -> clean public page (no staff nav), light padded canvas
//  - everything else -> staff SiteHeader + centered admin container
export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";

  if (pathname.startsWith("/rahbar")) {
    return <>{children}</>;
  }
  if (pathname.startsWith("/yozilish")) {
    return <div className="min-h-screen bg-slate-50 px-4 py-8">{children}</div>;
  }
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </>
  );
}
