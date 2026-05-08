#!/bin/sh
# Called by Nextcloud workflow on file events
INTEL_URL="http://172.21.30.100:8000/api/v1/file"

PAYLOAD=$(printf '{"user_id":"%s","file_path":"%s","file_size":%s,"action":"%s","ip_address":"%s"}' \
  "${NC_USER:-unknown}" \
  "${NC_FILE:-}" \
  "${NC_FILESIZE:-0}" \
  "${NC_ACTION:-unknown}" \
  "${NC_REMOTE_ADDRESS:-}")

wget -q --post-data="$PAYLOAD" \
     --header="Content-Type: application/json" \
     --timeout=3 \
     "$INTEL_URL" -O /dev/null 2>/dev/null || true
