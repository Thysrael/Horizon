"""CLI entry point for connecting Horizon to WeChat (iLink Bot).

Subcommands:

- ``login``  — scan a QR code with WeChat, then send the bot one message so
  Horizon can capture the conversation context it needs for pushes.
- ``status`` — show the saved session and optionally poll for new messages.
- ``test``   — preview or send a sample briefing through the saved session.
- ``listen`` — stay connected and answer chat commands (``日报``, ``1``/``2``,
  ``帮助``) as they arrive, for deployments that want the bot to feel live.
"""

import argparse
import asyncio
import io
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from .._cli import (
    add_data_dir_arguments,
    add_log_level_argument,
    default_language,
    load_config_or_exit,
)
from ..console_icons import IconStyle, get_icons
from ..logging_config import configure_logging
from ..models import WeChatConfig
from ..storage.manager import StorageManager
from .delivery import sample_briefing
from .wechat import (
    CONTEXT_MESSAGE_BUDGET,
    ILINK_BASE_URL,
    LONG_POLL_TIMEOUT,
    SESSION_FILE,
    STYLE_NAMES,
    Briefing,
    ILinkClient,
    ILinkError,
    WeChatNotifier,
    WeChatSession,
    redact_token,
    reply_language,
    welcome_text,
)

console = Console(stderr=True)
log = logging.getLogger(__name__)

QR_LOGIN_TIMEOUT = 480.0
MAX_QR_REFRESHES = 3
FIRST_MESSAGE_WAIT = 300.0
# Back-off for errcode -14 in the listener: 5, 10, ... up to 30 minutes.
SESSION_TIMEOUT_BACKOFF_BASE = 300
SESSION_TIMEOUT_BACKOFF_MAX = 1800


def _render_qr(content: str) -> None:
    """Print a scannable QR code in the terminal, falling back to the raw link."""
    try:
        import qrcode

        qr = qrcode.QRCode(border=1)
        qr.add_data(content)
        qr.make(fit=True)
        buffer = io.StringIO()
        qr.print_ascii(out=buffer, invert=True)
        console.print(buffer.getvalue(), markup=False, highlight=False)
    except Exception as e:  # pragma: no cover - depends on terminal/library
        console.print(f"[yellow]Could not render QR code in terminal ({e}).[/yellow]")
    console.print("If the QR code does not scan, open this link on another screen:")
    console.print(f"  [cyan]{content}[/cyan]\n")


async def _wait_for_login(client: ILinkClient, local_tokens: list[str]) -> Optional[dict]:
    """Run the QR login state machine. Returns the confirmed status payload."""
    qr = await client.get_bot_qrcode(local_tokens)
    qrcode_value = qr.get("qrcode")
    qr_content = qr.get("qrcode_img_content") or ""
    if not qrcode_value:
        console.print(f"[red]Unexpected QR response: {qr}[/red]")
        return None

    console.print("\n[bold]Scan this QR code with WeChat and confirm:[/bold]\n")
    _render_qr(qr_content)

    base_url = ILINK_BASE_URL
    verify_code: Optional[str] = None
    refreshes = 0
    scanned_announced = False
    loop = asyncio.get_event_loop()
    deadline = loop.time() + QR_LOGIN_TIMEOUT

    while loop.time() < deadline:
        started = loop.time()
        status = await client.get_qrcode_status(qrcode_value, verify_code=verify_code, base_url=base_url)
        state = status.get("status")

        if state == "wait":
            if loop.time() - started < 1.0:
                await asyncio.sleep(1)
        elif state == "scaned":
            if not scanned_announced:
                console.print("Scanned. Confirm the login on your phone...")
                scanned_announced = True
        elif state == "scaned_but_redirect":
            host = status.get("redirect_host")
            if host:
                base_url = host if host.startswith("http") else f"https://{host}"
                console.print(f"Redirected to {base_url}, continuing...")
        elif state == "need_verifycode":
            console.print("[yellow]WeChat asks for the verification code shown on your phone.[/yellow]")
            verify_code = input("Verification code: ").strip() or None
        elif state == "verify_code_blocked":
            console.print("[red]Too many failed verification attempts.[/red]")
            return None
        elif state == "expired":
            refreshes += 1
            if refreshes > MAX_QR_REFRESHES:
                console.print("[red]QR code expired too many times. Giving up.[/red]")
                return None
            console.print(f"QR code expired, refreshing ({refreshes}/{MAX_QR_REFRESHES})...")
            qr = await client.get_bot_qrcode(local_tokens)
            qrcode_value = qr.get("qrcode") or qrcode_value
            _render_qr(qr.get("qrcode_img_content") or qr_content)
            scanned_announced = False
            verify_code = None
        elif state == "binded_redirect":
            console.print(
                "[green]This bot is already connected with the saved token; "
                "keeping the existing session.[/green]"
            )
            return {"status": "binded_redirect"}
        elif state == "confirmed":
            return status
        else:
            console.print(f"[yellow]Unknown login status '{state}', continuing...[/yellow]")
            await asyncio.sleep(1)

    console.print("[red]Login timed out. Run 'horizon-wechat login' again.[/red]")
    return None


async def _wait_for_first_message(notifier: WeChatNotifier) -> bool:
    """Long-poll until the user messages the bot, which yields the first context token."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + FIRST_MESSAGE_WAIT
    while loop.time() < deadline:
        await notifier.refresh_context(timeout=LONG_POLL_TIMEOUT)
        if notifier.session is not None and notifier.session.ready:
            return True
    return False


async def _run_login(wechat_config: WeChatConfig, storage: StorageManager, force: bool) -> None:
    session_path = Path(storage.data_dir) / SESSION_FILE
    existing = None
    try:
        existing = WeChatSession.load(session_path)
    except (OSError, ValueError) as e:
        console.print(f"[yellow]Ignoring unreadable session file: {e}[/yellow]")

    if existing and existing.ready and not force:
        console.print(
            f"[green]Already connected[/green] as user {existing.user_id} "
            f"(session: {session_path}). Use --force to log in again."
        )
        return

    # Reporting the saved token lets WeChat answer "already connected" and keep the
    # old session; --force deliberately withholds it to obtain a fresh one.
    local_tokens = [existing.bot_token] if existing and not force else []
    status = await _wait_for_login(ILinkClient(), local_tokens)
    if status is None:
        sys.exit(1)

    if status.get("status") == "binded_redirect" and existing:
        session = existing
    else:
        token = status.get("bot_token")
        if not token:
            console.print(f"[red]Login confirmed but no bot_token returned: {status}[/red]")
            sys.exit(1)
        session = WeChatSession(
            bot_token=token,
            base_url=(status.get("baseurl") or ILINK_BASE_URL).rstrip("/"),
            bot_id=status.get("ilink_bot_id") or "",
            user_id=status.get("ilink_user_id") or "",
            logged_in_at=datetime.now(timezone.utc).isoformat(),
        )
        session.save(session_path)
        console.print(
            f"[green]Login confirmed.[/green] bot={session.bot_id or '?'} "
            f"user={session.user_id or '?'} token={redact_token(session.bot_token)}"
        )

    console.print(
        "\n[bold]One more step:[/bold] open the bot chat in WeChat and send it any message "
        "(for example 'hi').\nHorizon needs that message's context token to push "
        f"briefings. Waiting up to {int(FIRST_MESSAGE_WAIT // 60)} minutes...\n"
    )
    # Enabled regardless of config so the welcome message can be sent during setup.
    notifier = WeChatNotifier(wechat_config.model_copy(update={"enabled": True}), storage, console=console)
    try:
        got_message = await _wait_for_first_message(notifier)
    except ILinkError as e:
        console.print(f"[red]Failed while waiting for your message: {e.hint()}[/red]")
        sys.exit(1)

    if not got_message:
        console.print(
            "[yellow]No message received. Send the bot a message later and run "
            "'horizon-wechat status --refresh' to finish setup.[/yellow]"
        )
        return

    await notifier.send_text(welcome_text(reply_language(wechat_config)))
    console.print("[green]Connected![/green] A welcome message was sent to your WeChat.")
    console.print(f"Session saved to [cyan]{session_path}[/cyan].")
    if not wechat_config.enabled:
        console.print("Set [cyan]wechat.enabled = true[/cyan] in config.json to deliver daily briefings.")


async def _run_status(wechat_config: WeChatConfig, storage: StorageManager, refresh: bool) -> None:
    notifier = WeChatNotifier(wechat_config, storage, console=Console(stderr=True, quiet=True))
    if notifier.session is None:
        console.print(f"[yellow]No session at {notifier.session_path}. Run 'horizon-wechat login'.[/yellow]")
        sys.exit(1)

    if refresh:
        console.print("Polling for new messages (up to ~35s)...")
        try:
            changed = await notifier.refresh_context(timeout=LONG_POLL_TIMEOUT + 5)
        except ILinkError as e:
            console.print(f"[red]{e.hint()}[/red]")
            sys.exit(1)
        console.print("Context updated." if changed else "No new messages.")

    session = notifier.session
    chosen = session.style if session.style in STYLE_NAMES else ""
    rows = [
        ("Session file", str(notifier.session_path)),
        ("Enabled in config", str(wechat_config.enabled)),
        ("Base URL", session.base_url),
        ("Bot ID", session.bot_id or "?"),
        ("User ID", session.user_id or "?"),
        ("Bot token", redact_token(session.bot_token)),
        (
            "Context token",
            ("present" if session.context_token else "[yellow]missing[/yellow]")
            + (f" (updated {session.context_updated_at})" if session.context_updated_at else ""),
        ),
        ("Logged in", session.logged_in_at or "?"),
        ("Style", f"{chosen or wechat_config.style} " + ("(chosen in chat)" if chosen else "(config default)")),
        (
            "Replies left",
            f"{session.remaining_budget}/{CONTEXT_MESSAGE_BUDGET} for the current conversation "
            "(resets when you message the bot)",
        ),
    ]
    for label, value in rows:
        console.print(f"  [cyan]{label}:[/cyan] {value}")
    console.print(
        "\n[green]Ready to deliver.[/green]"
        if session.ready
        else "\n[yellow]Not ready: send the bot a message in WeChat, then rerun with --refresh.[/yellow]"
    )


async def _run_listen(wechat_config: WeChatConfig, storage: StorageManager) -> None:
    """Long-poll the bot inbox forever, answering chat commands as they arrive."""
    notifier = WeChatNotifier(wechat_config, storage, console=console)
    if notifier.session is None:
        sys.exit(1)
    if not notifier.session.ready:
        console.print(
            "[yellow]Session has no context token yet. Send the bot a message in WeChat; "
            "it will be picked up here.[/yellow]"
        )
    console.print(
        f"[green]Listening[/green] for WeChat messages as {notifier.session.user_id} "
        f"(style: {notifier.style().name}, replies left: {notifier.session.remaining_budget}). "
        "Press Ctrl+C to stop."
    )
    try:
        await notifier.client().notify_start()
    except (ILinkError, httpx.HTTPError) as e:
        log.warning("notifystart failed (continuing): %s", e)

    failures = timeouts = 0
    try:
        while True:
            try:
                changed = await notifier.refresh_context(timeout=LONG_POLL_TIMEOUT + 5)
            except (ILinkError, httpx.HTTPError) as e:
                if isinstance(e, ILinkError) and e.session_timeout:
                    # WeChat closed the receive session; it re-opens after a while.
                    timeouts += 1
                    delay = min(SESSION_TIMEOUT_BACKOFF_MAX, SESSION_TIMEOUT_BACKOFF_BASE * timeouts)
                    console.print(f"[yellow]{e.hint()} Retrying in {delay // 60} min.[/yellow]")
                    await asyncio.sleep(delay)
                    continue
                failures += 1
                log.warning("inbox poll failed (%d): %s", failures, e)
                await asyncio.sleep(min(30, 2 * failures))
                continue
            failures = timeouts = 0
            if changed:
                stamp = datetime.now().strftime("%H:%M:%S")
                console.print(
                    f"[{stamp}] inbox handled — style: {notifier.style().name}, "
                    f"replies left: {notifier.session.remaining_budget}/{CONTEXT_MESSAGE_BUDGET}"
                )
    finally:
        try:
            await notifier.client().notify_stop()
        except (ILinkError, httpx.HTTPError):
            pass


async def _run_test(
    wechat_config: WeChatConfig,
    storage: StorageManager,
    lang: str,
    dry_run: bool,
    style: Optional[str],
    icon_style: IconStyle,
) -> None:
    today, items, summarizer, summary = await sample_briefing(lang)
    effective_config = wechat_config.model_copy(update={"enabled": True}) if dry_run else wechat_config
    notifier = WeChatNotifier(
        effective_config,
        storage,
        console=Console(stderr=True, quiet=True) if dry_run else console,
        icons=get_icons(icon_style),
    )

    if dry_run:
        console.print(f"\n[bold yellow]── Dry Run (lang={lang}) ──[/bold yellow]")
        console.print(f"  [cyan]Session file:[/cyan] {notifier.session_path}")
        if effective_config.languages and lang not in effective_config.languages:
            console.print(
                f"  [yellow]Language '{lang}' is filtered out by "
                f"wechat.languages={effective_config.languages}.[/yellow]"
            )
            return
        active = notifier.style(style)
        console.print(f"  [cyan]Style:[/cyan] {active.name} — {active.describe(lang)}")
        bodies = Briefing.compose(summarizer, summary, items, len(items), today, lang).bodies(active)
        chunks = notifier.plan_chunks(bodies, lang)
        remaining = notifier.session.remaining_budget if notifier.session else CONTEXT_MESSAGE_BUDGET
        console.print(
            f"  [cyan]Messages to send:[/cyan] {len(chunks)} "
            f"(replies left for this conversation: {remaining}/{CONTEXT_MESSAGE_BUDGET})"
        )
        for index, chunk in enumerate(chunks, start=1):
            console.print(Panel(chunk, title=f"Message {index}/{len(chunks)}", border_style="green"))
        console.print("\n[green]Dry run complete. No message was sent.[/green]")
        return

    if not effective_config.enabled:
        console.print("[yellow]WeChat is not enabled in config.json.[/yellow]")
        console.print("Set [cyan]wechat.enabled = true[/cyan] or use --dry-run to preview.")
        sys.exit(1)

    console.print(f"\n[bold]── Sending Test Notification (lang={lang}) ──[/bold]")
    result = await notifier.send_daily_summary(
        summary=summary,
        important_items=items,
        all_items_count=len(items),
        date=today,
        lang=lang,
        summarizer=summarizer,
        style=style,
        remember=False,
    )
    if not result.sent:
        sys.exit(1)


def main() -> None:
    """CLI entry point for horizon-wechat."""
    parser = argparse.ArgumentParser(description="Connect Horizon to WeChat (iLink Bot) and test delivery")
    add_data_dir_arguments(parser)
    add_log_level_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Scan a QR code with WeChat to connect")
    login_parser.add_argument("--force", action="store_true", help="Log in again even if a session exists")

    status_parser = subparsers.add_parser("status", help="Show the saved WeChat session")
    status_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Poll for new inbound messages to refresh the conversation context",
    )

    subparsers.add_parser("listen", help="Stay connected and answer chat commands (日报 / 1 / 2 / 帮助) as they arrive")

    test_parser = subparsers.add_parser("test", help="Send or preview a sample briefing")
    test_parser.add_argument("--lang", default=None, help="Language to test (en or zh). Defaults to the first language in config.")
    test_parser.add_argument("--dry-run", action="store_true", help="Preview the rendered messages without sending anything.")
    test_parser.add_argument(
        "--style",
        default=None,
        choices=STYLE_NAMES,
        help="Override the message style (config default and chat choice) for this test.",
    )

    args = parser.parse_args()
    configure_logging(console, level=args.log_level)

    try:
        load_dotenv()
        storage, config = load_config_or_exit(console, args)
        wechat_config = config.wechat or WeChatConfig()

        if args.command == "login":
            asyncio.run(_run_login(wechat_config, storage, args.force))
        elif args.command == "status":
            asyncio.run(_run_status(wechat_config, storage, args.refresh))
        elif args.command == "listen":
            asyncio.run(_run_listen(wechat_config, storage))
        elif args.command == "test":
            asyncio.run(
                _run_test(
                    wechat_config,
                    storage,
                    default_language(args, config),
                    args.dry_run,
                    args.style,
                    config.display.icon_style,
                )
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
