#!/usr/bin/env bash

set -u

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd -- "$script_dir/../../../.." && pwd)"
repo_root="${HORIZON_REPO_ROOT:-$default_repo_root}"
runtime_dir="${NOTION_AGENT_RUNTIME_DIR:-$repo_root/.codex-runtime/notion-agent}"
local_url="${HORIZON_NOTION_AGENT_LOCAL_HEALTH_URL:-http://127.0.0.1:4782/healthz}"
public_url="${HORIZON_NOTION_AGENT_PUBLIC_HEALTH_URL:-https://horizen-agent.kaiosei.online/healthz}"
curl_timeout="${HORIZON_NOTION_AGENT_HEALTH_TIMEOUT_SECONDS:-15}"
exit_code=0

check_endpoint() {
    local label="$1"
    local url="$2"
    local response

    if response="$(curl --fail --silent --show-error --max-time "$curl_timeout" "$url" 2>&1)"; then
        printf '%s\tOK\t%s\n' "$label" "$response"
    else
        printf '%s\tFAIL\t%s\n' "$label" "$response" >&2
        exit_code=1
    fi
}

check_endpoint "local" "$local_url"
check_endpoint "public" "$public_url"

python3 - "$runtime_dir/events.sqlite3" <<'PY'
import json
import sqlite3
import sys
from pathlib import Path

path = Path(sys.argv[1])
counts = {
    "queued": 0,
    "running": 0,
    "succeeded": 0,
    "ignored": 0,
    "failed": 0,
}
if not path.is_file():
    print(f"durable_queue\tUNAVAILABLE\t{path}")
    raise SystemExit(0)

with sqlite3.connect(path) as connection:
    rows = connection.execute(
        "SELECT state, COUNT(*) FROM webhook_events GROUP BY state"
    ).fetchall()
counts.update({str(state): int(count) for state, count in rows})
print(
    "durable_queue\tOK\t"
    + json.dumps(counts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
)
PY

exit "$exit_code"
