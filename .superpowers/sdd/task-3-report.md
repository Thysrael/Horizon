# Task 3 report: wizard states and keyboards

## Scope delivered

- Added explicit `SourceForm` wizard states: `primary_input`, `value_review`,
  `options`, `field_input`, `summary`, and `delete_confirmation`.
- Added stable-source catalog, primary/review/options/edit/summary keyboards,
  plus the editability-aware source card keyboard.
- Added Russian wizard prompts and field-error templates.
- Kept the existing `SourceForm.config` state only as a compatibility bridge for
  the pre-existing legacy JSON handler. It is not used by the new wizard; its
  removal belongs with the handler replacement task.

## TDD evidence

1. Added `tests/infoservice/bot/test_source_wizard.py` before implementation.
2. RED run:
   `uv run pytest tests/infoservice/bot/test_source_wizard.py -v`
   failed during collection because `accepted_value_menu` did not exist.
3. Added the minimal presentation contracts.
4. The initial GREEN run exposed the legacy handler's import-time dependency on
   `SourceForm.config`; restored that compatibility-only state without adding
   wizard handler behavior.
5. GREEN run:
   `uv run pytest tests/infoservice/bot/test_source_wizard.py -v` — 5 passed.

## Verification

- Focused suite: `uv run pytest tests/infoservice/bot/test_source_wizard.py -v`
  — 5 passed.
- Full suite: `uv run pytest -v` — 525 passed, 13 skipped; one existing
  third-party `google.genai` deprecation warning.
- `git diff --check` — clean.
- Attempted `uv run ruff check ...`; it could not run because `ruff` is not
  installed in this environment.

## Changed files

- `src/infoservice/bot/states.py`
- `src/infoservice/bot/keyboards.py`
- `src/infoservice/bot/messages_ru.py`
- `tests/infoservice/bot/test_source_wizard.py`

## Self-review and concerns

- The catalog iterates `STABLE_SOURCE_TYPES`, preserving the Task 2 order and
  omitting beta integrations from creation.
- All new user-facing text is Russian and the callbacks are short static
  prefixes plus IDs, safely under Telegram's callback-data limit for UUID IDs.
- No source wizard handlers, repository code, schemas, JSONB, or worker code
  were changed.
- The legacy `config` state and JSON handler remain until the handler task;
  this is intentionally isolated so importing the current bot application and
  its existing tests stays functional.

## Review-fix evidence

### Scope

- Restored `source_catalog_menu(report_id, _capabilities=None)` compatibility:
  the legacy argument is accepted and ignored, while rendering still uses only
  `STABLE_SOURCE_TYPES`.
- Added `delete_confirmation_menu()` with confirmation, back, and cancel
  controls; `request_delete_source` now uses it.
- Deliberately retained `SourceForm.config` and did not change beta-source edit
  behavior, as both remain Task 4 dependencies.

### TDD evidence

1. Added both regression tests before the implementation changes.
2. RED run 1:
   `uv run pytest tests/infoservice/bot/test_source_wizard.py -v` failed at
   collection with `ImportError: cannot import name 'delete_confirmation_menu'`.
3. Added only the missing confirmation-keyboard factory.
4. RED run 2:
   `uv run pytest tests/infoservice/bot/test_source_wizard.py -v` collected 7
   tests and failed exactly at
   `test_legacy_open_catalog_signature_uses_stable_labels` with
   `TypeError: source_catalog_menu() takes 1 positional argument but 2 were given`.
5. Added the ignored legacy optional parameter and wired the existing delete
   confirmation handler to the new factory.
6. GREEN focused runs:
   - `uv run pytest tests/infoservice/bot/test_source_wizard.py -v` — 7 passed.
   - `uv run pytest tests/infoservice/bot/test_sources.py -v` — 12 passed.

### Final verification

- `uv run pytest -v` — 527 passed, 13 skipped, 1 existing third-party
  `google.genai` deprecation warning.
- `git diff --check` — clean.
