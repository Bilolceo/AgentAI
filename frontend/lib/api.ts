import type { MessageResponse, StartCallResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export async function startCall(fromNumber: string): Promise<StartCallResponse> {
  const res = await fetch(`${API_BASE}/simulation/calls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from_number: fromNumber }),
  });
  if (!res.ok) throw new Error(`startCall failed: ${res.status}`);
  return res.json();
}

export async function sendMessage(
  callId: number,
  text: string,
  language?: string,
): Promise<MessageResponse> {
  const res = await fetch(`${API_BASE}/simulation/calls/${callId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) throw new Error(`sendMessage failed: ${res.status}`);
  return res.json();
}
