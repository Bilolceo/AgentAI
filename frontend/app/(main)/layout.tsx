import Link from "next/link";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-5xl gap-6 px-4 py-3 text-sm font-medium">
          <Link href="/">Dashboard</Link>
          <Link href="/simulation">Simulyatsiya</Link>
          <Link href="/admin">Admin</Link>
          <Link href="/client" className="text-blue-600">Client Demo</Link>
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </>
  );
}
