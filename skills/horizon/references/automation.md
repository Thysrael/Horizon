# Scheduling and delivery

## Shared workflow

1. Identify the execution host, IANA timezone, desired local time, config/data
   paths, model credentials, and delivery channel. Reuse existing answers.
2. Follow `docs/configuration.md` for delivery configuration and preview commands.
   Use a real one-off run to check fetching, AI generation, and requested delivery.
3. Schedule the existing CLI, with absolute paths and a stable working directory:

   ```bash
   /absolute/path/to/uv run --directory /absolute/Horizon --no-sync horizon --hours 24
   ```

   Install/update dependencies with `uv sync` before using `--no-sync`. Add
   `--config` / `--data-dir` after `horizon` as required. The helper's staged
   `run_pipeline` is for generation and does not perform automatic delivery.
4. Persist the actual data directory across runs. History search needs prior
   `summaries/horizon-*.md`; email uses subscriber state; WeChat uses
   `wechat_session.json` and valid reply context. Follow the current WeChat guide
   for session and quota behavior.
5. Avoid overlapping jobs. Retain logs, inspect a completed execution, and report
   the next trigger in the chosen timezone. Distinguish installed configuration,
   scheduler activation, successful generation, and successful delivery.

The environment and filesystem visible to a scheduled account may differ from
the interactive terminal. Use absolute executable paths and verify that account
can read `.env`, config, profiles, and its persistent data directory. When reusing
the host assistant's API key, configure a persistent credential source for the
scheduled process or container, such as the existing `.env` or the host's secret
injection mechanism. A variable available only during an agent turn does not
establish unattended access. Verify a one-off run in the actual scheduled or
container environment, rather than relying on an interactive-shell check.
Preview output can contain resolved webhook URLs/headers; keep credentials out
of the user-facing transcript.

## GitHub Actions

Read `.github/workflows/daily-summary.yml.disabled` and
`.github/workflows/deploy-docs.yml`. The former is a disabled generation template;
the latter deploys docs on pushes and does not itself generate news.

- Adapt the disabled template into an active `.yml` workflow for the user's
  repository. Configure its actual config file, secret names, extras, permissions,
  and Pages destination. Preserve existing unrelated jobs.
- Use the default branch for scheduled events and keep `workflow_dispatch` for a
  one-off check. Set a concurrency group so two runs do not publish simultaneously.
- Interpret the cron expression itself, not an old comment. With no timezone
  field, GitHub uses UTC. For example, `0 0 * * *` means 08:00 Asia/Shanghai.
  Check current GitHub syntax if using its timezone field. Scheduled execution
  can be delayed; describe the configured trigger separately from actual arrival.
- Restore history into the data directory before generation and persist new
  history afterwards. Existing Pages posts on `gh-pages` are not automatically
  present in the runner's `data/summaries`.
- Verify a dispatched run's logs and output, then the requested Pages URL or
  notification. A locally written workflow is not yet an active scheduled job.

Current syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

## Linux server and Docker

Use the host's existing scheduler. For systemd, define a `Type=oneshot` service
with `WorkingDirectory`, an absolute `ExecStart`, and the intended user. Pair it
with a timer containing, for example:

```ini
[Timer]
OnCalendar=*-*-* 08:00:00 Asia/Shanghai
Persistent=true

[Install]
WantedBy=timers.target
```

Check the expression with `systemd-analyze calendar`, reload the appropriate
system/user manager, enable the timer, and inspect `list-timers` and journal
output. For user timers, account logout behavior matters; choose a system service
or configured user lingering when it must run unattended. For cron, verify the
installed cron implementation's timezone support and provide overlap prevention.

Docker Compose is a one-shot execution target, not a scheduler. Run it from the
host scheduler with the correct project directory:

```bash
docker compose --project-directory /absolute/Horizon run --rm horizon --hours 24
```

Inspect `docker-compose.yml` and `Dockerfile` for mounts, runtime user, and extras.
The existing data bind mount preserves state; custom Profiles require a rebuilt
image or an appropriate read-only mount. Container-local Pages files also need a
persistent mount/export if they will be published. Verify behavior from the host
account that actually launches Docker.

Current timer semantics: https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html

## Personal computer

Use the OS-native scheduler and the shared execution/data rules above:

| OS | Configure | Verify |
| --- | --- | --- |
| macOS | A LaunchAgent in `~/Library/LaunchAgents/`, with argument-array `ProgramArguments`, `WorkingDirectory`, `StartCalendarInterval`, and absolute log paths | `plutil -lint`, register with `launchctl bootstrap`, inspect `launchctl print` and a test execution |
| Linux | A user systemd service/timer as above, or the existing cron implementation | Calendar interpretation, login/logout behavior, timer status and journal |
| Windows | Task Scheduler action with full `uv.exe` path, quoted arguments and Start-in directory; daily trigger; intended account and missed-run/overlap policy | Task properties, next run time, last result, and generated output |

For local-time schedulers, record the machine's timezone and account for sleep,
shutdown, logout, and daylight-saving behavior. Configure wake/missed-run options
according to the user's needs; do not claim an offline machine will deliver on
time. For a different timezone, consult the platform's current scheduler options
instead of applying a fixed offset across DST changes.

Use the installed `launchctl`/`launchd.plist` manual pages on macOS and current
Task Scheduler documentation on Windows when generating their configuration.
