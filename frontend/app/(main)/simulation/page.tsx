import { SimulationChat } from "@/components/SimulationChat";

export default function SimulationPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Qo'ng'iroq simulyatsiyasi</h1>
      <p className="text-gray-600">
        AI qabulxona operatori bilan matnli suhbat. Xavfsizlik to'sig'i (tibbiy maslahat,
        shoshilinch holat) avtomatik ishlaydi va operatorga uzatadi.
      </p>
      <SimulationChat />
    </div>
  );
}
