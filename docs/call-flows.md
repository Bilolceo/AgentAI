# Call Flows

> Detailed business rules come from `TZ_AI_CallCenter_v2.1.docx`. This is the MVP
> baseline; refine per the TZ.

## 1. Information request (safe)
User asks about hours / services / address → RAG retrieves clinic info → AI replies.
Audit: `call_started`, `language_detected`, `ai_response_generated`.

## 2. Booking
User wants an appointment → BookingService creates a `pending` booking.
TODO (TZ): availability/slot rules, working hours, confirmation, Google Calendar/CRM.
Audit: `booking_created`, later `reminder_scheduled`.

## 3. Medical-advice request (blocked)
Diagnosis / medicine / dosage / treatment → SafetyGuardService deflects + transfers
to a human operator. The AI never gives medical advice.
Audit: `safety_guard_triggered`, `operator_transfer_requested`.

## 4. Emergency
Urgent symptoms (chest pain, can't breathe, bleeding, unconscious, ...) →
verbatim guidance to call **103** / nearest hospital, transfer, stop normal flow.
Audit: `safety_guard_triggered (emergency)`, `operator_transfer_requested`.

## 5. Operator transfer (generic)
Complex/out-of-scope cases → OperatorTransferService marks the call `transferred`.
(Real call bridging is added with telephony post-MVP.)
