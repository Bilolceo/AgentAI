#!/usr/bin/env bash
set -euo pipefail
# Bootstrap a super_admin (dev/test only), log in, and seed the demo KB.
API="${API:-http://localhost:8000/api/v1}"
EMAIL="${ADMIN_EMAIL:-admin@clinic.uz}"
PASS="${ADMIN_PASSWORD:-Admin12345}"

echo "1) bootstrap super_admin ($EMAIL)"
curl -sS -X POST "$API/auth/dev-bootstrap-super-admin" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"full_name\":\"Admin\"}" >/dev/null || true

echo "2) login"
TOKEN=$(curl -sS -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

echo "3) seed knowledge base"
curl -sS -X POST "$API/admin/knowledge/seed" -H "Authorization: Bearer $TOKEN"
echo
echo "Done. Login at http://localhost:3000/login as $EMAIL"
