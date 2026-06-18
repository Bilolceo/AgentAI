import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AI Call-Center — Admin",
  description: "Clinic AI voice receptionist admin dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <body>
        <header className="border-b bg-white">
          <nav className="mx-auto flex max-w-5xl gap-6 px-4 py-3 text-sm font-medium">
            <Link href="/">Dashboard</Link>
            <Link href="/simulation">Simulyatsiya</Link>
            <Link href="/admin">Admin</Link>
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
