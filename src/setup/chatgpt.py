"""Command-line account management for Sign in with ChatGPT."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from ..ai.chatgpt_auth import ChatGPTAuth, MANAGE_USAGE_URL
from ..models import AIConfig, AIProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Connect Horizon to your ChatGPT plan")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize this runtime's host ID before importing credentials")
    login = commands.add_parser("login", help="Continue with ChatGPT, or reconnect a saved account")
    login.add_argument("--account", help="Saved client ID to reconnect")
    login.add_argument("--new-account", action="store_true")
    login.add_argument("--enable-plan", action="store_true", help="Request consent for ChatGPT plan usage")
    login.add_argument("--no-browser", action="store_true", help="Print the sign-in URL to open manually on this machine")
    for name in ("logout", "status", "models", "check"):
        command = commands.add_parser(name)
        command.add_argument("--account", help="Saved client ID (defaults to the active account)")
        if name == "check":
            command.add_argument("--model", required=True, help="Model slug from the models command")
    commands.add_parser("accounts", help="List saved account registrations")
    commands.add_parser("select", help="Select a saved account").add_argument("account")
    args = parser.parse_args()
    auth = ChatGPTAuth()
    try:
        if args.command == "init":
            print(json.dumps(auth.initialize(), indent=2))
        elif args.command == "login":
            print("Continue with ChatGPT in your browser.")
            kwargs = {"open_browser": lambda url: False} if args.no_browser else {}
            session = auth.sign_in(
                args.account, new_account=args.new_account, enable_plan=args.enable_plan, **kwargs,
            )
            print(json.dumps(session, indent=2))
            if not session["plan_usage"]:
                print("Plan usage is not enabled. Run horizon-chatgpt login --enable-plan to authorize it.")
            print(f"Manage usage: {MANAGE_USAGE_URL}")
        elif args.command == "logout":
            confirmed = auth.sign_out(args.account)
            print("Signed out locally.")
            if not confirmed:
                print(f"Remote revocation was not confirmed. Disconnect the app in ChatGPT settings: {MANAGE_USAGE_URL}")
        elif args.command == "status":
            print(json.dumps(auth.status(args.account), indent=2))
            print(f"Manage usage: {MANAGE_USAGE_URL}")
        elif args.command == "accounts":
            print(json.dumps(auth.accounts(), indent=2))
        elif args.command == "select":
            auth.select(args.account)
            print("Active ChatGPT account updated. Refresh the model selection with horizon-chatgpt models.")
        elif args.command == "models":
            print(json.dumps(auth.models(args.account), indent=2))
        elif args.command == "check":
            from ..ai.chatgpt import ChatGPTClient
            client = ChatGPTClient(AIConfig(
                provider=AIProvider.OPENAI_CHATGPT, model=args.model, chatgpt_account=args.account,
            ), auth=auth)

            async def check():
                try:
                    result = await client.complete(
                        'Respond with exactly the JSON object {"ok": true}.', 'Verify the connection.',
                    )
                    if json.loads(result) != {"ok": True}:
                        raise RuntimeError("ChatGPT completed the request but did not return the expected JSON.")
                finally:
                    await client.client.close()

            asyncio.run(check())
            print("ChatGPT plan usage verified: completed inference returned valid JSON.")
    except (RuntimeError, ValueError, OSError) as exc:
        print(f"ChatGPT: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
