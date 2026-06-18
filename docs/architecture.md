# Architecture

## Pilot MVP (current)
Text-based call simulation — no telephony yet.

```
Client / Admin UI
   │  POST /api/v1/simulation/calls            → start call (CallSessionService)
   │  POST /api/v1/simulation/calls/{id}/message
   ▼
CallSessionService
   ├─ SafetyGuardService   (medical guardrails — runs FIRST, pure logic)
   ├─ AIService
   │     ├─ RAGService     (pgvector / MVP keyword search over knowledge base)
   │     └─ AIProvider     (MockAIProvider now; ClaudeAIProvider later)
   ├─ OperatorTransferService  (escalate risky/complex cases)
   └─ AuditLogService      (call_started, language_detected, ai_response_generated,
                            safety_guard_triggered, operator_transfer_requested, ...)
```

Persistence: PostgreSQL (SQLAlchemy 2.0 async) + pgvector. Redis/Celery for
reminders and async ingest (post-MVP).

## Safety flow
Every user utterance is evaluated by `SafetyGuardService` before reaching the AI
provider:
- **emergency** symptoms → verbatim 103 guidance, transfer, stop normal flow
- diagnosis / medicine / dosage / treatment request → safe deflection + operator transfer
- otherwise → allow → RAG-grounded AI reply

## Post-MVP (later)
Real telephony: Twilio Media Streams (WebSocket) ↔ Azure STT/TTS (uz-UZ/ru-RU),
wired through the same `AIService`. Google Calendar / CRM booking. SMS/Telegram
reminders via `NotificationService` + Celery.
