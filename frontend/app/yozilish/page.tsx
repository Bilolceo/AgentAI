"use client";

import { useEffect, useMemo, useState } from "react";
import { LanguageSwitcher, useLanguage } from "@/lib/i18n";
import {
  getPublicServices,
  getPublicDoctors,
  getPublicSlots,
  createPublicBooking,
  BookingApiError,
  type PublicService,
  type PublicDoctor,
  type PublicBookingResult,
} from "@/lib/public-booking";

type Step = 1 | 2 | 3 | 4 | 5;

function ymdLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function BookingPage() {
  const { t, tSpec } = useLanguage();

  const [step, setStep] = useState<Step>(1);
  const [services, setServices] = useState<PublicService[]>([]);
  const [servicesLoaded, setServicesLoaded] = useState(false);
  const [specialty, setSpecialty] = useState<string | null>(null);

  const [doctors, setDoctors] = useState<PublicDoctor[]>([]);
  const [doctor, setDoctor] = useState<PublicDoctor | null>(null);

  const [date, setDate] = useState<string>(ymdLocal(new Date()));
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [time, setTime] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [notes, setNotes] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PublicBookingResult | null>(null);

  const today = useMemo(() => ymdLocal(new Date()), []);
  const maxDate = useMemo(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return ymdLocal(d);
  }, []);

  useEffect(() => {
    getPublicServices()
      .then(setServices)
      .catch(() => setServices([]))
      .finally(() => setServicesLoaded(true));
  }, []);

  // Load doctors when entering step 2.
  useEffect(() => {
    if (step !== 2 || !specialty) return;
    getPublicDoctors(specialty).then(setDoctors).catch(() => setDoctors([]));
  }, [step, specialty]);

  // Load slots whenever doctor or date changes on step 3.
  useEffect(() => {
    if (step !== 3 || !doctor) return;
    setSlotsLoading(true);
    setTime(null);
    getPublicSlots(doctor.id, date)
      .then((r) => setSlots(r.slots))
      .catch(() => setSlots([]))
      .finally(() => setSlotsLoading(false));
  }, [step, doctor, date]);

  function pickService(s: PublicService) {
    setSpecialty(s.specialty);
    setDoctor(null);
    setStep(2);
  }
  function pickDoctor(d: PublicDoctor) {
    setDoctor(d);
    setStep(3);
  }

  function errMessage(code: string): string {
    const key = `book_err_${code}`;
    const msg = t(key);
    return msg === key ? t("book_err_generic") : msg;
  }

  async function submit() {
    if (!doctor || !time) return;
    if (!name.trim() || !phone.trim()) {
      setError(t("book_required"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await createPublicBooking({
        doctor_id: doctor.id,
        date,
        time,
        patient_name: name.trim(),
        patient_phone: phone.trim(),
        service: specialty ?? undefined,
        notes: notes.trim() || undefined,
      });
      setResult(res);
      setStep(5);
    } catch (e) {
      setError(e instanceof BookingApiError ? errMessage(e.code) : t("book_err_generic"));
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setStep(1);
    setSpecialty(null);
    setDoctor(null);
    setTime(null);
    setName("");
    setPhone("");
    setNotes("");
    setResult(null);
    setError(null);
    setDate(today);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold text-slate-900">{t("book_brand")}</div>
          <div className="text-xs text-slate-500">{t("book_brand_sub")}</div>
        </div>
        <LanguageSwitcher />
      </header>

      {step < 5 && (
        <>
          <div className="mb-2 text-center">
            <h1 className="text-xl font-semibold text-slate-900">{t("book_hero_title")}</h1>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{t("book_hero_sub")}</p>
          </div>
          <Stepper step={step} />
        </>
      )}

      <div className="mt-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        {/* Step 1 — service */}
        {step === 1 && (
          <Section title={t("book_choose_service")}>
            {!servicesLoaded ? (
              <Muted>...</Muted>
            ) : services.length === 0 ? (
              <Muted>{t("book_no_services")}</Muted>
            ) : (
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {services.map((s) => (
                  <button
                    key={s.specialty}
                    onClick={() => pickService(s)}
                    className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3 text-left transition hover:border-blue-500 hover:bg-blue-50"
                  >
                    <span className="font-medium text-slate-800">{tSpec(s.specialty)}</span>
                    <span className="text-xs text-slate-400">{s.doctor_count} {t("book_doctors_count")}</span>
                  </button>
                ))}
              </div>
            )}
          </Section>
        )}

        {/* Step 2 — doctor */}
        {step === 2 && (
          <Section title={t("book_choose_doctor")}>
            {doctors.length === 0 ? (
              <Muted>{t("book_no_doctors")}</Muted>
            ) : (
              <div className="grid grid-cols-1 gap-2">
                {doctors.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => pickDoctor(d)}
                    className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3 text-left transition hover:border-blue-500 hover:bg-blue-50"
                  >
                    <span>
                      <span className="block font-medium text-slate-800">{d.full_name}</span>
                      <span className="block text-xs text-slate-400">{tSpec(d.specialty)}</span>
                    </span>
                    {d.room && <span className="text-xs text-slate-400">{d.room}</span>}
                  </button>
                ))}
              </div>
            )}
            <BackBar onBack={() => setStep(1)} t={t} />
          </Section>
        )}

        {/* Step 3 — date + time */}
        {step === 3 && (
          <Section title={t("book_choose_date")}>
            <input
              type="date"
              value={date}
              min={today}
              max={maxDate}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <div className="mt-4 mb-1 text-sm font-medium text-slate-700">{t("book_choose_time")}</div>
            {slotsLoading ? (
              <Muted>...</Muted>
            ) : slots.length === 0 ? (
              <Muted>{t("book_no_slots")}</Muted>
            ) : (
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                {slots.map((s) => (
                  <button
                    key={s}
                    onClick={() => setTime(s)}
                    className={`rounded-lg border px-2 py-2 text-sm transition ${
                      time === s
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-slate-200 text-slate-700 hover:border-blue-400"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="mt-5 flex items-center justify-between">
              <button onClick={() => setStep(2)} className="text-sm text-slate-500 hover:text-slate-800">
                {t("book_back")}
              </button>
              <button
                onClick={() => setStep(4)}
                disabled={!time}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                {t("book_next")}
              </button>
            </div>
          </Section>
        )}

        {/* Step 4 — contact + summary */}
        {step === 4 && doctor && (
          <Section title={t("book_step_contact")}>
            <div className="mb-4 rounded-lg bg-slate-50 p-3 text-sm">
              <div className="mb-1 font-medium text-slate-700">{t("book_summary")}</div>
              <SummaryRow label={t("book_step_service")} value={tSpec(specialty)} />
              <SummaryRow label={t("book_step_doctor")} value={doctor.full_name} />
              <SummaryRow label={t("book_step_time")} value={`${date} · ${time}`} />
            </div>
            <Field label={t("book_name")}>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("book_name_ph")}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </Field>
            <Field label={t("book_phone")} hint={t("book_phone_hint")}>
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder={t("book_phone_ph")}
                inputMode="tel" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </Field>
            <Field label={t("book_notes")}>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={t("book_notes_ph")}
                rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </Field>
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
            <div className="mt-5 flex items-center justify-between">
              <button onClick={() => setStep(3)} className="text-sm text-slate-500 hover:text-slate-800">
                {t("book_back")}
              </button>
              <button onClick={submit} disabled={busy}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
                {busy ? t("book_submitting") : t("book_submit")}
              </button>
            </div>
          </Section>
        )}

        {/* Step 5 — success */}
        {step === 5 && result && (
          <div className="py-4 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-2xl text-green-600">
              ✓
            </div>
            <h2 className="text-lg font-semibold text-slate-900">{t("book_success_title")}</h2>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">{t("book_success_sub")}</p>
            <p className="mx-auto mt-2 max-w-sm text-xs text-slate-400">{t("book_sms_note")}</p>
            <div className="mx-auto mt-4 max-w-xs rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
              <SummaryRow label={t("book_reference")} value={result.reference} />
              <SummaryRow label={t("book_step_doctor")} value={result.doctor_name} />
              <SummaryRow label={t("book_step_time")} value={`${date} · ${time}`} />
              <SummaryRow label="" value={t("book_status_pending")} badge />
            </div>
            <button onClick={reset} className="mt-5 rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
              {t("book_new_one")}
            </button>
          </div>
        )}
      </div>

      <p className="mt-4 text-center text-xs text-slate-400">{t("book_brand")} · {today}</p>
    </div>
  );
}

const STEP_KEYS = ["book_step_service", "book_step_doctor", "book_step_time", "book_step_contact"];

function Stepper({ step }: { step: Step }) {
  const { t } = useLanguage();
  return (
    <div className="mt-4 flex items-center justify-center gap-1.5">
      {STEP_KEYS.map((k, i) => {
        const n = i + 1;
        const active = step === n;
        const done = step > n;
        return (
          <div key={k} className="flex items-center gap-1.5">
            <div className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium ${
              done ? "bg-green-500 text-white" : active ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-500"
            }`}>
              {done ? "✓" : n}
            </div>
            <span className={`hidden text-xs sm:inline ${active ? "font-medium text-slate-800" : "text-slate-400"}`}>
              {t(k)}
            </span>
            {n < STEP_KEYS.length && <span className="mx-1 h-px w-4 bg-slate-200" />}
          </div>
        );
      })}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-semibold text-slate-700">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="mb-3 block">
      <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-400">{hint}</span>}
    </label>
  );
}

function SummaryRow({ label, value, badge }: { label: string; value: string; badge?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 py-0.5">
      {label ? <span className="text-slate-500">{label}</span> : <span />}
      {badge ? (
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">{value}</span>
      ) : (
        <span className="font-medium text-slate-800">{value}</span>
      )}
    </div>
  );
}

function Muted({ children }: { children: React.ReactNode }) {
  return <p className="rounded-lg border border-dashed border-slate-200 p-4 text-center text-sm text-slate-400">{children}</p>;
}

function BackBar({ onBack, t }: { onBack: () => void; t: (k: string) => string }) {
  return (
    <div className="mt-4">
      <button onClick={onBack} className="text-sm text-slate-500 hover:text-slate-800">{t("book_back")}</button>
    </div>
  );
}
