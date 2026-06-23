import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="text-gray-600">
        Pilot MVP — matnli qo'ng'iroq simulyatsiyasi. Qo'ng'iroqlar tarixi, transkriptlar
        va bronlar bu yerda ko'rsatiladi.
      </p>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card title="Qo'ng'iroqlar" href="/calls" hint="Tarix va transkriptlar (admin API)" />
        <Card title="Bilim bazasi" href="/knowledge" hint="Klinika ma'lumotlari" />
        <Card title="Simulyatsiya" href="/simulation" hint="AI bilan matnli test" />
      </div>
    </div>
  );
}

function Card({ title, href, hint }: { title: string; href: string; hint: string }) {
  return (
    <Link href={href} className="rounded-lg border bg-white p-4 hover:shadow">
      <div className="font-medium">{title}</div>
      <div className="mt-1 text-sm text-gray-500">{hint}</div>
    </Link>
  );
}
