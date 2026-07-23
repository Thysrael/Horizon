# Task 1: Register Commands and Add Global Navigation — Report

## Implementation summary

- Added the default Telegram command menu with eight canonical commands and Russian descriptions; registration runs after `Bot` construction and before polling.
- Replaced the `/start` text equality filter with aiogram 3 `CommandStart()`.
- Added state-independent `/menu`, `/help`, `/settings`, and `/cancel` routes using aiogram 3 `Command` filters, plus their inline-button navigation callbacks.
- Added Russian help, settings, and cancellation copy; the main and settings menus now use the required hybrid Russian labels.
- Added `replace_or_answer()` so callback-based screens edit the existing screen and fall back to sending a message if Telegram rejects an edit.
- Registered navigation before all FSM-specific routers, so the global navigation remains available while a user is in a wizard state. `/menu` and `/cancel` clear the FSM without persisting draft data.

## TDD evidence

### RED

Command run before the new production modules existed:

```bash
uv run pytest tests/infoservice/bot/test_commands.py -v
```

Result: collection failed as expected with:

```text
ModuleNotFoundError: No module named 'src.infoservice.bot.commands'
```

### GREEN

After the implementation:

```bash
uv run pytest tests/infoservice/bot/test_commands.py tests/infoservice/bot/test_onboarding.py -v
```

Result: `14 passed in 2.48s`.

## Verification

```bash
uv run pytest
```

Result: `503 passed, 13 skipped, 1 warning in 6.58s`.

The sole warning is an existing third-party deprecation warning from `google.genai.types` under Python 3.14.

## Files changed

- `.superpowers/sdd/task-1-report.md`
- `src/infoservice/bot/commands.py`
- `src/infoservice/bot/ui.py`
- `src/infoservice/bot/handlers/navigation.py`
- `src/infoservice/bot/app.py`
- `src/infoservice/bot/handlers/start.py`
- `src/infoservice/bot/keyboards.py`
- `src/infoservice/bot/messages_ru.py`
- `tests/infoservice/bot/test_commands.py`
- `tests/infoservice/bot/test_onboarding.py`

## Self-review

- Verified command order, Russian descriptions, and default-scope registration.
- Verified the command handlers clear FSM state where required and render the prescribed buttons/text.
- Verified callback navigation consistently calls `replace_or_answer()`.
- Verified the navigation router is included before stateful routers and command registration precedes polling.
- Ran `git diff --check` successfully before the full suite.

## Concerns

- The command menu includes `/reports`, `/newreport`, and `/sources` as specified, while this slice only adds the explicitly required global command handlers (`/menu`, `/help`, `/settings`, `/cancel`). Direct command routing for the report/source workflows remains outside this Task 1 brief.
