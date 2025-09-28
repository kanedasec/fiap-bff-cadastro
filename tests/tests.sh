#!/usr/bin/env bash
set -euo pipefail

BFF_URL="${BFF_URL:-http://localhost:8010}"

banner() { echo -e "\n==== $* ===="; }

REQ_ID="manual-$(date +%s)"

banner "Health"
curl -fsS -H "X-Request-ID: $REQ_ID" "$BFF_URL/healthz" | jq .
curl -fsS -H "X-Request-ID: $REQ_ID" "$BFF_URL/readyz" | jq .

banner "Signup (novo usuário)"
EMAIL="signup.$(date +%s)@example.com"
curl -fsS -H "X-Request-ID: $REQ_ID" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"Passw0rd!\",\"full_name\":\"Test User\",\"phone\":\"11999999999\",\"document\":\"12345678900\"}" \
  "$BFF_URL/signup" | tee /tmp/signup.json | jq .

KC_ID=$(jq -r '.keycloak_user_id' /tmp/signup.json)
BUYER_ID=$(jq -r '.buyer_id' /tmp/signup.json)

echo "Keycloak user: $KC_ID"
echo "Buyer id: $BUYER_ID"

banner "Retry (idempotência - deve retornar buyer válido)"
curl -fsS -H "X-Request-ID: $REQ_ID" -H "Content-Type: application/json" \
  -d "{\"keycloak_user_id\":\"$KC_ID\",\"email\":\"$EMAIL\",\"full_name\":\"Test User\",\"phone\":\"11999999999\",\"document\":\"12345678900\"}" \
  "$BFF_URL/signup/retry" | jq .

echo -e "\n==== FIM ====\n"
