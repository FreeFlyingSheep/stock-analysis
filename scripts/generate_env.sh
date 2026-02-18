#!/bin/bash
# Generate a .env file from .env.example by replacing CHANGEME placeholders with random secrets.
set -euo pipefail

input_path=".env.example"
output_path=".env"

if [[ ! -f "$input_path" ]]; then
  echo "Input file not found: $input_path" >&2
  exit 1
fi

rand_hex() {
  local bytes="$1"
  openssl rand -hex "$bytes"
}

rand_b64() {
  local bytes="$1"
  openssl rand -base64 "$bytes"
}

ARCH=$(docker version --format '{{.Server.Arch}}')

DB_PASSWORD="$(rand_hex 16)"
MINIO_PASSWORD="$(rand_hex 16)"
REDIS_PASSWORD="$(rand_hex 16)"
GRAFANA_PASSWORD="$(rand_hex 16)"
LANGFUSE_DB_PASSWORD="$(rand_hex 16)"
LANGFUSE_CLICKHOUSE_PASSWORD="$(rand_hex 16)"
LANGFUSE_INIT_USER_PASSWORD="$(rand_hex 16)"

LANGFUSE_NEXTAUTH_SECRET="$(rand_b64 48)"
LANGFUSE_SALT="$(rand_hex 16)"
LANGFUSE_ENCRYPTION_KEY="$(rand_hex 32)"

LANGFUSE_PUBLIC_HEX="$(rand_hex 16)"
LANGFUSE_SECRET_HEX="$(rand_hex 32)"
LANGFUSE_INIT_PROJECT_PUBLIC_KEY="pk-$LANGFUSE_PUBLIC_HEX"
LANGFUSE_INIT_PROJECT_SECRET_KEY="sk-$LANGFUSE_SECRET_HEX"
LANGFUSE_OTLP_AUTH_BASE64="$(printf '%s' "$LANGFUSE_INIT_PROJECT_PUBLIC_KEY:$LANGFUSE_INIT_PROJECT_SECRET_KEY" | base64 | tr -d '\n')"

tmp_output="$(mktemp)"
trap 'rm -f "$tmp_output"' EXIT

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line//CHANGEME_architecture/$ARCH}"
  line="${line//CHANGEME_database_password/$DB_PASSWORD}"
  line="${line//CHANGEME_minio_password/$MINIO_PASSWORD}"
  line="${line//CHANGEME_redis_password/$REDIS_PASSWORD}"
  line="${line//CHANGEME_grafana_password/$GRAFANA_PASSWORD}"
  line="${line//CHANGEME_base64_pk_colon_sk/$LANGFUSE_OTLP_AUTH_BASE64}"
  line="${line//CHANGEME_langfuse_admin_password/$LANGFUSE_INIT_USER_PASSWORD}"
  line="${line//CHANGEME_32_HEX/$LANGFUSE_PUBLIC_HEX}"
  line="${line//CHANGEME_64_HEX/$LANGFUSE_SECRET_HEX}"
  line="${line//CHANGEME_nextauth_secret/$LANGFUSE_NEXTAUTH_SECRET}"
  line="${line//CHANGEME_salt_hex/$LANGFUSE_SALT}"
  line="${line//CHANGEME_64_hex_encryption_key/$LANGFUSE_ENCRYPTION_KEY}"
  line="${line//CHANGEME_langfuse_db_password/$LANGFUSE_DB_PASSWORD}"
  line="${line//CHANGEME_clickhouse_password/$LANGFUSE_CLICKHOUSE_PASSWORD}"
  printf '%s\n' "$line" >> "$tmp_output"
done < "$input_path"

mv "$tmp_output" "$output_path"
trap - EXIT

if grep -q "CHANGEME" "$output_path"; then
  echo "Warning: Some CHANGEME placeholders remain. Update them manually." >&2
else
  echo "Wrote $output_path"
fi
