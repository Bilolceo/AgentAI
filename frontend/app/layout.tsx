import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hospital by Khusanov — Admin",
  description: "Clinic AI voice receptionist admin dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz">
      <body>{children}</body>
    </html>
  );
}
