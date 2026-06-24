// Public (customer-facing) booking API client. No auth headers — these
// endpoints are intentionally open. Backend error `detail` codes are surfaced
// so the UI can show a localized message.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export interface PublicService {
  specialty: string;
  doctor_count: number;
}

export interface PublicDoctor {
  id: number;
  full_name: string;
  specialty: string | null;
  room: string | null;
}

export interface PublicSlots {
  doctor_id: number;
  date: string;
  slots: string[];
}

export interface PublicBookingInput {
  doctor_id: number;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM
  patient_name: string;
  patient_phone: string;
  service?: string;
  notes?: string;
}

export interface PublicBookingResult {
  ok: boolean;
  reference: string;
  status: string;
  doctor_name: string;
  scheduled_at: string | null;
}

// Error whose `code` is the backend `detail` (e.g. "slot_taken", "invalid_phone").
export class BookingApiError extends Error {
  code: string;
  constructor(code: string) {
    super(code);
    this.code = code;
  }
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new BookingApiError(String(res.status));
  return res.json();
}

export async function createPublicCallback(input: { name: string; phone: string; message?: string }): Promise<void> {
  const res = await fetch(`${API_BASE}/public/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    let code = String(res.status);
    try {
      const body = await res.json();
      if (body?.detail) code = String(body.detail);
    } catch {
      // keep status code
    }
    throw new BookingApiError(code);
  }
}

export function getPublicServices(): Promise<PublicService[]> {
  return getJSON<PublicService[]>("/public/services");
}

export function getPublicDoctors(specialty?: string): Promise<PublicDoctor[]> {
  const q = specialty ? `?specialty=${encodeURIComponent(specialty)}` : "";
  return getJSON<PublicDoctor[]>(`/public/doctors${q}`);
}

export function getPublicSlots(doctorId: number, date: string): Promise<PublicSlots> {
  return getJSON<PublicSlots>(`/public/slots?doctor_id=${doctorId}&date=${encodeURIComponent(date)}`);
}

export async function createPublicBooking(input: PublicBookingInput): Promise<PublicBookingResult> {
  const res = await fetch(`${API_BASE}/public/appointments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    let code = String(res.status);
    try {
      const body = await res.json();
      if (body?.detail) code = String(body.detail);
    } catch {
      // keep status code as the error code
    }
    throw new BookingApiError(code);
  }
  return res.json();
}
