#!/usr/bin/env bash

set -euo pipefail

usage() {
    printf 'Usage: %s (--run-id ID | --latest) [--follow]\n' "${0##*/}"
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd -- "$script_dir/../../../.." && pwd)"
repo_root="${HORIZON_REPO_ROOT:-$default_repo_root}"
runtime_dir="${NOTION_AGENT_RUNTIME_DIR:-$repo_root/.codex-runtime/notion-agent}"
runs_dir="$runtime_dir/runs"
run_id=""
latest=false
follow=false

while (($#)); do
    case "$1" in
        --run-id)
            if (($# < 2)); then
                usage >&2
                exit 2
            fi
            run_id="$2"
            shift 2
            ;;
        --latest)
            latest=true
            shift
            ;;
        --follow)
            follow=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

if [[ -n "$run_id" && "$latest" == true ]]; then
    usage >&2
    exit 2
fi

if [[ -n "$run_id" ]]; then
    clean_run_id="$(printf '%s' "$run_id" | tr -cd '[:alnum:]' | tr '[:upper:]' '[:lower:]')"
    run_dir="$runs_dir/$clean_run_id"
elif [[ "$latest" == true ]]; then
    shopt -s nullglob
    task_files=("$runs_dir"/*/task.json)
    if ((${#task_files[@]} == 0)); then
        printf 'No claimed Horizon Notion Agent runs found under %s\n' "$runs_dir" >&2
        exit 1
    fi
    latest_task="$(ls -1t -- "${task_files[@]}" | head -n 1)"
    run_dir="$(dirname -- "$latest_task")"
else
    usage >&2
    exit 2
fi

if [[ ! -d "$run_dir" ]]; then
    printf 'Run directory not found: %s\n' "$run_dir" >&2
    exit 1
fi

printf 'run_dir=%s\n' "$run_dir"

python3 - "$run_dir/task.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    print("task=unavailable")
    raise SystemExit(0)

task = json.loads(path.read_text(encoding="utf-8"))
for key in ("job_id", "title", "risk", "allowed_paths"):
    value = str(task.get(key) or "").replace("\r", " ").replace("\n", " ")
    print(f"{key}={value}")
PY

mapfile -t queue_info < <(
    python3 - "$run_dir/task.json" "$runtime_dir/events.sqlite3" <<'PY'
import sqlite3
import sys
from pathlib import Path

task_path = Path(sys.argv[1])
queue_path = Path(sys.argv[2])
if not task_path.is_file() or not queue_path.is_file():
    print("unknown")
    print("")
    raise SystemExit(0)

import json

task = json.loads(task_path.read_text(encoding="utf-8"))
job_id = str(task.get("job_id") or "")
with sqlite3.connect(queue_path) as connection:
    row = connection.execute(
        """
        SELECT state, result
        FROM webhook_events
        WHERE execution_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (job_id,),
    ).fetchone()
if row is None:
    print("unknown")
    print("")
else:
    print(str(row[0]))
    print(str(row[1]).replace("\r", " ").replace("\n", " ")[:500])
PY
)
queue_state="${queue_info[0]:-unknown}"
queue_result="${queue_info[1]:-}"
printf 'queue_state=%s\n' "$queue_state"
if [[ -n "$queue_result" ]]; then
    printf 'queue_result=%s\n' "$queue_result"
fi

if [[ "$queue_state" =~ ^(succeeded|failed|ignored)$ ]]; then
    stage="$queue_state"
elif [[ -f "$run_dir/pr-body.md" ]]; then
    stage="publishing-or-finished"
elif [[ -f "$run_dir/verification.log" ]]; then
    stage="verification"
elif [[ -f "$run_dir/codex-result.json" ]]; then
    stage="codex-completed"
elif [[ -f "$run_dir/codex.jsonl" ]]; then
    stage="codex"
elif [[ -f "$run_dir/prompt.md" ]]; then
    stage="preparing-codex"
else
    stage="claimed"
fi
printf 'stage=%s\n' "$stage"

for artifact in \
    task.json \
    prompt.md \
    codex.jsonl \
    codex-result.json \
    verification.log \
    pr-body.md; do
    if [[ -f "$run_dir/$artifact" ]]; then
        printf 'artifact=%s\n' "$artifact"
    fi
done

if [[ "$follow" == true ]]; then
    if [[ -f "$run_dir/verification.log" ]]; then
        log_path="$run_dir/verification.log"
    else
        log_path="$run_dir/codex.jsonl"
    fi
    printf 'following=%s\n' "$log_path"
    exec tail -F "$log_path"
fi
