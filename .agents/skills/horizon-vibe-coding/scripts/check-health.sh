#!/usr/bin/env bash

set -u

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

exit "$exit_code"
