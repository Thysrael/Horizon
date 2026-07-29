"""Tests for catch-up, idempotency, and retry in the Codex daily runner."""

import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.codex_daily import (
    MAX_CATCHUP_HOURS,
    LockUnavailable,
    SingleInstanceLock,
    _codex_is_logged_in,
    _load_and_validate_codex_config,
    _runner_paths,
    calculate_fetch_hours,
    is_due,
    main,
    parse_daily_at,
    resolve_timezone,
    run_once,
    should_skip_today,
)


def _write_config(
    path: Path,
    *,
    provider: str = "codex",
    api_key_env: str = "",
    provider_chain: str | None = None,
) -> None:
    ai = {
        "provider": provider,
        "model": "default",
        "api_key_env": api_key_env,
    }
    if provider_chain is not None:
        ai["provider_chain"] = provider_chain
    path.write_text(
        json.dumps(
            {
                "ai": ai,
                "sources": {},
                "filtering": {"time_window_hours": 24},
            }
        ),
        encoding="utf-8",
    )


def _config_stub(hours: int = 24):
    return SimpleNamespace(
        filtering=SimpleNamespace(time_window_hours=hours)
    )


@pytest.mark.parametrize("value", ["00:00", "08:30", "23:59"])
def test_parse_daily_at_accepts_strict_24_hour_time(value):
    assert parse_daily_at(value).strftime("%H:%M") == value


@pytest.mark.parametrize("value", ["8:00", "24:00", "12:60", "noon"])
def test_parse_daily_at_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="HH:MM"):
        parse_daily_at(value)


def test_explicit_iana_timezones_are_supported():
    assert str(resolve_timezone("UTC")) == "UTC"
    assert str(resolve_timezone("America/New_York")) == "America/New_York"


def test_unknown_timezone_is_rejected():
    with pytest.raises(ValueError, match="Unknown IANA timezone"):
        resolve_timezone("Mars/Olympus")


def test_daily_run_is_not_due_before_start_time():
    now = datetime(2026, 7, 29, 7, 59, tzinfo=timezone.utc)

    assert not is_due(now, time(8, 0))
    assert is_due(now.replace(hour=8), time(8, 0))


def test_success_is_compared_in_the_selected_timezone():
    los_angeles = resolve_timezone("America/Los_Angeles")
    now = datetime(2026, 7, 28, 18, 0, tzinfo=los_angeles)
    state = {"last_success_at": "2026-07-29T00:30:00+00:00"}

    assert should_skip_today(state, now, los_angeles)
    assert not should_skip_today(
        {"last_success_at": "2026-07-28T00:30:00+00:00"},
        now,
        los_angeles,
    )


def test_fetch_window_covers_downtime_with_overlap():
    now = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)
    last_success = now - timedelta(hours=49, minutes=10)

    assert calculate_fetch_hours(24, now, last_success) == 52


def test_fetch_window_uses_configured_default_and_caps_catchup():
    now = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)

    assert calculate_fetch_hours(24, now, now - timedelta(hours=20)) == 24
    assert (
        calculate_fetch_hours(24, now, now - timedelta(days=30))
        == MAX_CATCHUP_HOURS
    )
    assert calculate_fetch_hours(500, now, None) == MAX_CATCHUP_HOURS


def test_single_instance_lock_rejects_a_second_owner(tmp_path):
    lock_path = tmp_path / "daily.lock"

    with SingleInstanceLock(lock_path):
        with pytest.raises(LockUnavailable):
            with SingleInstanceLock(lock_path):
                pass

    with SingleInstanceLock(lock_path):
        pass


def test_login_status_accepts_output_from_either_stream():
    assert _codex_is_logged_in("Logged in using ChatGPT", "")
    assert _codex_is_logged_in("", "Logged in using ChatGPT")


def test_codex_preflight_accepts_logged_in_keyless_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    monkeypatch.setattr("src.codex_daily.shutil.which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr("src.ai.client.shutil.which", lambda _: "/usr/bin/codex")
    run = SimpleNamespace(
        returncode=0,
        stdout="Logged in using ChatGPT",
        stderr="",
    )
    monkeypatch.setattr("src.codex_daily.subprocess.run", lambda *a, **k: run)

    config = _load_and_validate_codex_config(config_path)

    assert config.ai.provider.value == "codex"
    assert config.ai.api_key_env == ""


@pytest.mark.parametrize(
    ("provider", "api_key_env", "provider_chain", "message"),
    [
        ("openai", "OPENAI_API_KEY", None, "Expected ai.provider=codex"),
        ("codex", "SOME_KEY", None, "must not require an API key"),
        ("codex", "", "codex,ollama", "does not support provider_chain"),
    ],
)
def test_codex_preflight_rejects_nonlocal_config(
    tmp_path,
    provider,
    api_key_env,
    provider_chain,
    message,
):
    config_path = tmp_path / "config.json"
    _write_config(
        config_path,
        provider=provider,
        api_key_env=api_key_env,
        provider_chain=provider_chain,
    )

    with pytest.raises(RuntimeError, match=message):
        _load_and_validate_codex_config(config_path)


def test_codex_preflight_rejects_logged_out_session(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    monkeypatch.setattr("src.codex_daily.shutil.which", lambda _: "/usr/bin/codex")
    run = SimpleNamespace(returncode=1, stdout="", stderr="Not logged in")
    monkeypatch.setattr("src.codex_daily.subprocess.run", lambda *a, **k: run)

    with pytest.raises(RuntimeError, match="Codex is not logged in"):
        _load_and_validate_codex_config(config_path)


def test_runner_skips_before_daily_time_without_starting_pipeline(
    tmp_path,
    monkeypatch,
    capsys,
):
    config_path = tmp_path / "config.json"
    validate = pytest.fail
    monkeypatch.setattr(
        "src.codex_daily._load_and_validate_codex_config",
        validate,
    )
    now = datetime(2026, 7, 29, 7, 59, tzinfo=timezone.utc)

    result = run_once(
        config_path=config_path,
        run_timezone=timezone.utc,
        daily_at=time(8, 0),
        now=now,
    )

    assert result == 0
    assert capsys.readouterr().out.startswith("SKIP:")


def test_runner_success_is_idempotent_and_records_changed_summaries(
    tmp_path,
    monkeypatch,
    capsys,
):
    config_path = tmp_path / "config.json"
    now = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("src.codex_daily._now", lambda tz: now)
    validate_calls = []
    monkeypatch.setattr(
        "src.codex_daily._load_and_validate_codex_config",
        lambda path: validate_calls.append(path) or _config_stub(),
    )

    async def successful_pipeline(path, hours):
        summaries = path.parent / "summaries"
        summaries.mkdir()
        (summaries / "horizon-2026-07-29-en.md").write_text(
            "# Summary",
            encoding="utf-8",
        )
        return {"status": "success", "attempted": 1, "failed": 0}

    monkeypatch.setattr(
        "src.codex_daily._run_pipeline",
        successful_pipeline,
    )

    first = run_once(
        config_path=config_path,
        run_timezone=timezone.utc,
        daily_at=time(8, 0),
        now=now,
    )
    second = run_once(
        config_path=config_path,
        run_timezone=timezone.utc,
        daily_at=time(8, 0),
        now=now,
    )

    state = json.loads(
        _runner_paths(config_path)["state"].read_text(encoding="utf-8")
    )
    output = capsys.readouterr().out
    assert first == 0
    assert second == 0
    assert len(validate_calls) == 1
    assert "DONE: report:" in output
    assert "SKIP: Horizon Codex already completed" in output
    assert state["last_attempt_status"] == "success"
    assert state["last_summaries"] == [
        str(
            (
                tmp_path
                / "summaries"
                / "horizon-2026-07-29-en.md"
            ).resolve()
        )
    ]


def test_force_runs_before_daily_time(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    now = datetime(2026, 7, 29, 7, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("src.codex_daily._now", lambda tz: now)
    monkeypatch.setattr(
        "src.codex_daily._load_and_validate_codex_config",
        lambda path: _config_stub(),
    )

    async def successful_pipeline(path, hours):
        return {"status": "success"}

    monkeypatch.setattr(
        "src.codex_daily._run_pipeline",
        successful_pipeline,
    )

    assert (
        run_once(
            config_path=config_path,
            run_timezone=timezone.utc,
            daily_at=time(8, 0),
            force=True,
            now=now,
        )
        == 0
    )


def test_failure_preserves_success_state_and_next_invocation_retries(
    tmp_path,
    monkeypatch,
    capsys,
):
    config_path = tmp_path / "config.json"
    now = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)
    old_success = "2026-07-27T10:00:00+00:00"
    paths = _runner_paths(config_path)
    paths["state"].write_text(
        json.dumps({"last_success_at": old_success}),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.codex_daily._now", lambda tz: now)
    monkeypatch.setattr(
        "src.codex_daily._load_and_validate_codex_config",
        lambda path: _config_stub(),
    )
    attempts = 0

    async def flaky_pipeline(path, hours):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary failure")
        return {"status": "success"}

    monkeypatch.setattr("src.codex_daily._run_pipeline", flaky_pipeline)

    failed = run_once(
        config_path=config_path,
        run_timezone=timezone.utc,
        daily_at=time(8, 0),
        now=now,
    )
    failed_state = json.loads(paths["state"].read_text(encoding="utf-8"))
    retried = run_once(
        config_path=config_path,
        run_timezone=timezone.utc,
        daily_at=time(8, 0),
        now=now,
    )
    final_state = json.loads(paths["state"].read_text(encoding="utf-8"))

    assert failed == 1
    assert retried == 0
    assert attempts == 2
    assert failed_state["last_success_at"] == old_success
    assert failed_state["last_attempt_status"] == "failure"
    assert final_state["last_attempt_status"] == "success"
    assert capsys.readouterr().out.count("FAILED:") == 1


def test_partial_source_failure_is_retried(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    now = datetime(2026, 7, 29, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("src.codex_daily._now", lambda tz: now)
    monkeypatch.setattr(
        "src.codex_daily._load_and_validate_codex_config",
        lambda path: _config_stub(),
    )

    async def partial_pipeline(path, hours):
        return {"status": "partial_failure", "failed": 1}

    monkeypatch.setattr("src.codex_daily._run_pipeline", partial_pipeline)

    assert (
        run_once(
            config_path=config_path,
            run_timezone=timezone.utc,
            daily_at=time(8, 0),
            now=now,
        )
        == 1
    )


def test_main_reports_invalid_timezone_and_daily_time():
    with pytest.raises(SystemExit) as timezone_error:
        main(["--timezone", "Mars/Olympus"])
    with pytest.raises(SystemExit) as time_error:
        main(["--daily-at", "8:00"])

    assert timezone_error.value.code == 2
    assert time_error.value.code == 2
