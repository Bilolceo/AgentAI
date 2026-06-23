import "./globals.css";
import type { Metadata } from "next";
import { LanguageProvider } from "@/lib/i18n";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Urologiya klinikasi — AI registrator",
  description: "Urologiya klinikasi AI ovozli registrator boshqaruv paneli",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <body className="bg-slate-50 text-slate-900">
        <LanguageProvider>
          <AppShell>{children}</AppShell>
        </LanguageProvider>
      </body>
    </html>
  );
}
