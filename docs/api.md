# API (v1)

Base: `/api/v1`. Admin endpoints require `X-API-Key` header.

## Health
- `GET /health` → `{"status":"ok"}`
- `GET /ready` → DB connectivity check

## Simulation (MVP, no auth)
- `POST /simulation/calls` — body `{ "from_number": "+99890...", "to_number?": "clinic" }` → `{ "call_id": 1 }`
- `POST /simulation/calls/{call_id}/message` — body `{ "text": "...", "language?": "uz-UZ|ru-RU" }`
  → `{ "reply", "action": "allow|transfer|emergency", "category", "transferred", "language" }`
- `POST /simulation/calls/{call_id}/end` → 204

## Admin (X-API-Key)
- `GET /calls`, `GET /calls/{id}` — call list + transcripts
- `GET /knowledge`, `POST /knowledge/ingest` — knowledge base
- `GET /bookings`, `POST /bookings` — appointments

## Example
```bash
CID=$(curl -s -X POST localhost:8000/api/v1/simulation/calls \
  -H 'Content-Type: application/json' -d '{"from_number":"+998901112233"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["call_id"])')

curl -s -X POST localhost:8000/api/v1/simulation/calls/$CID/message \
  -H 'Content-Type: application/json' -d '{"text":"Nafas ololmayapman"}'
# → action: "emergency", transferred: true, reply mentions 103
```
