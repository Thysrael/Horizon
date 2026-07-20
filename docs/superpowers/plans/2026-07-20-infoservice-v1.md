# InfoService v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить fork Horizon в публичный мультитенантный Telegram-бот, где пользователи со своими DeepSeek-ключами создают независимые отчёты, источники, правила и расписания.

**Architecture:** Существующее Horizon-ядро остаётся библиотекой сбора и AI-обработки. Новый пакет `src/infoservice` добавляет aiogram-интерфейс, PostgreSQL-хранилище, шифрование credentials, scheduler и worker; процессы координируются транзакциями PostgreSQL без Redis. Horizon получает runtime API key через явный интерфейс и возвращает результат без обязательной файловой/webhook-доставки.

**Tech Stack:** Python 3.11+, aiogram 3.25, Pydantic 2/pydantic-settings, SQLAlchemy 2 async, asyncpg, Alembic, PostgreSQL 16, cryptography/Fernet, croniter, httpx, pytest/pytest-asyncio/respx, Docker Compose.

## Global Constraints

- Сохранить MIT-лицензию, copyright Horizon, ссылку на upstream и рабочие команды `horizon`, `horizon-mcp`, `horizon-wizard`, `horizon-webhook`.
- Главный интерфейс v1 — личный чат Telegram на русском; групповые чаты отправляют пользователя в личный чат. Язык отчёта выбирается между `ru` (по умолчанию) и `en`.
- Один пользователь: максимум 5 отчётов, 30 источников на отчёт, 30 итоговых материалов, один выполняющийся запуск и не чаще одного запуска отчёта в час.
- Пользовательский prompt — максимум 2 000 символов и только дополнительное правило оценки/сводки.
- История запусков хранится 30 дней; сырой контент после выполнения не сохраняется.
- DeepSeek key хранится только в ciphertext, удаляется из Telegram после ввода и никогда не попадает в env, логи или исключения.
- Модель DeepSeek по умолчанию — `deepseek-v4-flash`; имя модели хранится с credential и не зашивается в pipeline.
- Стабильные источники: RSS, Telegram public channels, Hacker News, GitHub. Beta: Reddit, Google News, GDELT, OSSInsight. Twitter и OpenBB показываются только при включённой server capability.
- Расписания: daily, weekdays, weekly либо пятичастный cron в IANA timezone; минимальный интервал — один час.
- Baseline перед изменениями: `uv run --extra dev pytest -q` проходит полностью.

## Locked File Map

- `src/infoservice/settings.py` — только environment-конфигурация процесса.
- `src/infoservice/db/` — ORM, session factory, миграционные metadata и репозитории.
- `src/infoservice/security/credentials.py` — только шифрование, маскирование и redaction.
- `src/infoservice/sources/catalog.py` — capability/форма/валидация source JSON.
- `src/infoservice/scheduling/` — вычисление расписаний и транзакционный claim задач.
- `src/infoservice/execution/` — DTO, Horizon adapter и worker loop.
- `src/infoservice/delivery/telegram.py` — рендеринг и отправка готового результата.
- `src/infoservice/bot/` — aiogram application, handlers, FSM, клавиатуры и русские сообщения.
- `alembic/` — одна общая схема PostgreSQL; schema-per-tenant не используется.

---

### Task 1: Runtime configuration and package entrypoints

**Files:**
- Modify: `pyproject.toml`
- Create: `src/infoservice/__init__.py`
- Create: `src/infoservice/settings.py`
- Create: `tests/infoservice/test_settings.py`

**Interfaces:**
- Produces: `Settings()` with `database_url`, `telegram_bot_token`, `app_encryption_key`, `deepseek_default_model`, concurrency, retention and capability flags.
- Produces console scripts: `infoservice-bot`, `infoservice-scheduler`, `infoservice-worker`.

- [ ] **Step 1: Add a failing settings test**

```python
def test_settings_require_secrets(monkeypatch):
    for name in ("DATABASE_URL", "TELEGRAM_BOT_TOKEN", "APP_ENCRYPTION_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_settings_parse_capabilities(monkeypatch, valid_env):
    monkeypatch.setenv("ENABLE_TWITTER", "true")
    settings = Settings()
    assert settings.enable_twitter is True
    assert settings.max_reports_per_user == 5
    assert settings.run_retention_days == 30
```

- [ ] **Step 2: Verify the tests fail before implementation**

Run: `uv run pytest tests/infoservice/test_settings.py -q`

Expected: collection fails because `src.infoservice.settings` does not exist.

- [ ] **Step 3: Add dependencies, scripts and validated settings**

Add dependencies with bounded major versions:

```toml
"aiogram>=3.25,<4",
"sqlalchemy>=2.0,<3",
"asyncpg>=0.30,<1",
"alembic>=1.16,<2",
"pydantic-settings>=2.10,<3",
"cryptography>=45,<47",
"croniter>=6,<7",
```

Add dev dependencies `pytest-asyncio>=1,<2` and `respx>=0.22,<1`. Add scripts:

```toml
infoservice-bot = "src.infoservice.bot.app:main"
infoservice-scheduler = "src.infoservice.scheduling.service:main"
infoservice-worker = "src.infoservice.execution.worker:main"
```

Implement settings with these exact defaults:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    telegram_bot_token: SecretStr
    app_encryption_key: SecretStr
    worker_concurrency: int = Field(default=2, ge=1, le=16)
    stale_run_minutes: int = Field(default=30, ge=5)
    scheduler_poll_seconds: int = Field(default=30, ge=5)
    run_retention_days: int = Field(default=30, ge=1)
    max_reports_per_user: int = 5
    max_sources_per_report: int = 30
    deepseek_default_model: str = "deepseek-v4-flash"
    enable_twitter: bool = False
    enable_openbb: bool = False
    apify_token: SecretStr | None = None
```

- [ ] **Step 4: Sync and run focused tests**

Run: `uv sync --extra dev && uv run pytest tests/infoservice/test_settings.py -q`

Expected: all settings tests pass; `uv.lock` changes deterministically.

- [ ] **Step 5: Commit the runtime foundation**

```bash
git add pyproject.toml uv.lock src/infoservice tests/infoservice/test_settings.py
git commit -m "feat: add InfoService runtime settings"
```

---

### Task 2: PostgreSQL schema and migrations

**Files:**
- Create: `src/infoservice/db/base.py`
- Create: `src/infoservice/db/__init__.py`
- Create: `src/infoservice/db/models.py`
- Create: `src/infoservice/db/session.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260720_01_initial_schema.py`
- Create: `docker-compose.test.yml`
- Create: `tests/infoservice/db/conftest.py`
- Create: `tests/infoservice/db/test_schema.py`

**Interfaces:**
- Produces: `Base`, `create_session_factory(database_url) -> async_sessionmaker[AsyncSession]`.
- Produces ORM types: `User`, `LLMCredential`, `Report`, `Source`, `ReportRun`, `SourceRunResult` and their string enums.

- [ ] **Step 1: Write failing PostgreSQL schema tests**

```python
async def test_user_and_report_cascade(session):
    user = User(telegram_user_id=1001, chat_id=1001, timezone="Europe/Moscow")
    report = Report(user=user, name="AI", schedule_kind="daily", schedule_value="09:00")
    session.add(user)
    await session.commit()
    await session.delete(user)
    await session.commit()
    assert await session.get(Report, report.id) is None


async def test_scheduled_run_is_idempotent(session, report):
    scheduled_for = datetime(2026, 7, 20, 6, tzinfo=timezone.utc)
    session.add_all([
        ReportRun(report_id=report.id, trigger="scheduled", scheduled_for=scheduled_for),
        ReportRun(report_id=report.id, trigger="scheduled", scheduled_for=scheduled_for),
    ])
    with pytest.raises(IntegrityError):
        await session.commit()
```

- [ ] **Step 2: Start PostgreSQL and verify failure**

Run: `docker compose -f docker-compose.test.yml up -d postgres && TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/db/test_schema.py -q`

Expected: tests fail because ORM and migration files do not exist.

- [ ] **Step 3: Implement ORM with database-enforced ownership and limits-friendly indexes**

Use UUID primary keys and timezone-aware timestamps. Lock these constraints:

```python
UniqueConstraint("telegram_user_id", name="uq_users_telegram_user_id")
UniqueConstraint("chat_id", name="uq_users_chat_id")
UniqueConstraint("user_id", "provider", name="uq_llm_credentials_user_provider")
UniqueConstraint("report_id", "scheduled_for", name="uq_report_runs_schedule")
CheckConstraint("ai_score_threshold >= 0 AND ai_score_threshold <= 10")
CheckConstraint("max_items >= 1 AND max_items <= 30")
```

`Source.config` is JSONB; all foreign keys use `ON DELETE CASCADE`. Add indexes on `reports(user_id)`, `reports(enabled, next_run_at)`, `sources(report_id)` and `report_runs(status, created_at)`.

- [ ] **Step 4: Configure async Alembic and create the explicit initial migration**

`alembic/env.py` imports `Base.metadata` and uses `async_engine_from_config`; migration `upgrade()` creates all six tables, PostgreSQL enums, constraints and indexes. `downgrade()` drops tables in reverse dependency order and then enums.

- [ ] **Step 5: Apply migration and run schema tests**

Run:

```bash
DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/db/test_schema.py -q
```

Expected: migration succeeds and all schema tests pass.

- [ ] **Step 6: Commit the persistent model**

```bash
git add src/infoservice/db alembic.ini alembic docker-compose.test.yml tests/infoservice/db
git commit -m "feat: add PostgreSQL persistence model"
```

---

### Task 3: Tenant-safe repositories and product limits

**Files:**
- Create: `src/infoservice/db/repositories/users.py`
- Create: `src/infoservice/db/repositories/__init__.py`
- Create: `src/infoservice/db/repositories/credentials.py`
- Create: `src/infoservice/db/repositories/reports.py`
- Create: `src/infoservice/db/repositories/runs.py`
- Create: `src/infoservice/errors.py`
- Create: `tests/infoservice/db/test_repositories.py`

**Interfaces:**
- Produces: `UserRepository.get_or_create(telegram_user_id, chat_id) -> User`.
- Produces: `ReportRepository.get_owned(report_id, user_id) -> Report`, `create`, `update`, `delete`, `add_source`.
- Produces domain errors: `NotFound`, `LimitExceeded`, `Conflict` with safe user-facing messages.

- [ ] **Step 1: Write failing isolation and limit tests**

```python
async def test_get_owned_hides_foreign_report(report_repo, user_a, user_b):
    report = await report_repo.create(user_a.id, CreateReport(name="AI"))
    with pytest.raises(NotFound):
        await report_repo.get_owned(report.id, user_b.id)


async def test_report_limit_is_enforced(report_repo, user_a):
    for index in range(5):
        await report_repo.create(user_a.id, CreateReport(name=f"R{index}"))
    with pytest.raises(LimitExceeded, match="5"):
        await report_repo.create(user_a.id, CreateReport(name="R6"))
```

- [ ] **Step 2: Verify focused tests fail**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/db/test_repositories.py -q`

Expected: imports fail for repository modules.

- [ ] **Step 3: Implement repositories with ownership in every query**

Use predicates shaped like:

```python
stmt = select(Report).where(Report.id == report_id, Report.user_id == user_id)
report = (await session.execute(stmt)).scalar_one_or_none()
if report is None:
    raise NotFound("Отчёт не найден")
```

Count and lock the owning user row before enforcing report/source limits so concurrent callbacks cannot exceed limits. Never expose a repository method `get_report(report_id)` without `user_id` except in the worker-only run repository.

- [ ] **Step 4: Run repository and schema tests**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/db -q`

Expected: all database tests pass.

- [ ] **Step 5: Commit repositories**

```bash
git add src/infoservice/db/repositories src/infoservice/errors.py tests/infoservice/db
git commit -m "feat: enforce tenant isolation and limits"
```

---

### Task 4: Encrypted BYOK credentials and runtime AI keys

**Files:**
- Create: `src/infoservice/security/credentials.py`
- Create: `src/infoservice/security/__init__.py`
- Create: `src/infoservice/llm/deepseek.py`
- Create: `src/infoservice/llm/__init__.py`
- Modify: `src/ai/client.py`
- Modify: `src/orchestrator.py`
- Create: `tests/infoservice/security/test_credentials.py`
- Create: `tests/infoservice/llm/test_deepseek.py`
- Modify: `tests/test_minimax_client.py`
- Modify: `tests/test_chained_client.py`

**Interfaces:**
- Produces: `CredentialCipher.encrypt(str) -> str`, `decrypt(str) -> str`, `mask(str) -> str`, `redact(str) -> str`.
- Produces: `DeepSeekVerifier.verify(api_key: str) -> VerifiedCredential` using `GET /models` with a ten-second timeout.
- Changes: `create_ai_client(config: AIConfig, *, api_key: str | None = None) -> AIClient`.

- [ ] **Step 1: Write failing secret-safety tests**

```python
def test_cipher_round_trip_without_plaintext(cipher):
    token = cipher.encrypt("sk-secret-value")
    assert "sk-secret-value" not in token
    assert cipher.decrypt(token) == "sk-secret-value"
    assert cipher.mask("sk-secret-value") == "sk-…alue"


def test_explicit_key_does_not_touch_environment(monkeypatch, deepseek_config):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    client = create_ai_client(deepseek_config, api_key="sk-user")
    assert client.client.api_key == "sk-user"
    assert os.getenv("DEEPSEEK_API_KEY") is None
```

- [ ] **Step 2: Verify the tests fail**

Run: `uv run pytest tests/infoservice/security/test_credentials.py tests/infoservice/llm/test_deepseek.py -q`

Expected: missing modules and unsupported `api_key` keyword.

- [ ] **Step 3: Implement encryption, masking and verification**

Decode `APP_ENCRYPTION_KEY` as a Fernet key at startup and fail closed on invalid format. `DeepSeekVerifier` sends only `Authorization: Bearer <key>` and returns model ids; map 401/403 to `InvalidCredential`, 429/5xx/timeouts to `CredentialVerificationUnavailable`. Never include response bodies or the key in exception text.

- [ ] **Step 4: Thread explicit keys through every AI client factory**

Change internal constructors to accept `api_key: str | None`, resolve it before env fallback, and pass it through `HorizonOrchestrator(..., runtime_api_key=None)`. Chained providers remain env-only and are disabled by the InfoService adapter; legacy calls without `api_key` behave unchanged.

- [ ] **Step 5: Run secret, AI and legacy client tests**

Run: `uv run pytest tests/infoservice/security tests/infoservice/llm tests/test_minimax_client.py tests/test_chained_client.py tests/test_azure_client.py -q`

Expected: all tests pass and legacy env behavior is unchanged.

- [ ] **Step 6: Commit credential support**

```bash
git add src/infoservice/security src/infoservice/llm src/ai/client.py src/orchestrator.py tests
git commit -m "feat: support encrypted user LLM credentials"
```

---

### Task 5: Source catalog and validated JSONB configs

**Files:**
- Create: `src/infoservice/sources/catalog.py`
- Create: `src/infoservice/sources/__init__.py`
- Create: `src/infoservice/sources/schemas.py`
- Create: `tests/infoservice/sources/test_catalog.py`

**Interfaces:**
- Produces: `SourceCatalog.available(settings) -> list[SourceCapability]`.
- Produces: `SourceCatalog.validate(source_type: str, raw: dict, settings) -> BaseModel`.
- Uses existing Horizon source config models after bot-specific normalization.

- [ ] **Step 1: Write failing catalog tests for stable, beta and optional sources**

```python
def test_optional_sources_follow_capabilities(settings):
    names = {item.type for item in SourceCatalog.available(settings)}
    assert {"rss", "telegram", "hackernews", "github"} <= names
    assert "twitter" not in names
    assert "openbb" not in names


def test_telegram_accepts_only_public_username(settings):
    parsed = SourceCatalog.validate("telegram", {"channel": "@example"}, settings)
    assert parsed.channel == "example"
    with pytest.raises(SourceValidationError):
        SourceCatalog.validate("telegram", {"channel": "https://t.me/+private"}, settings)
```

- [ ] **Step 2: Verify the tests fail**

Run: `uv run pytest tests/infoservice/sources/test_catalog.py -q`

Expected: source catalog imports fail.

- [ ] **Step 3: Implement explicit schemas and capability metadata**

Each `SourceCapability` contains `type`, Russian label, stability (`stable`/`beta`/`optional`), input fields and model factory. Normalize RSS URL/name/category, Telegram username, GitHub `repo_releases`/`user_events`, HN thresholds, Reddit subreddit/user, Google News query/locale, GDELT query, OSSInsight languages, Twitter user list and OpenBB watchlist.

Reject unknown keys via `extra="forbid"`; URL-bearing types reuse `HttpUrl` and Horizon SSRF validation before execution.

- [ ] **Step 4: Run catalog and existing scraper model tests**

Run: `uv run pytest tests/infoservice/sources tests/test_rss.py tests/test_telegram.py tests/test_reddit.py tests/test_gdelt.py tests/test_google_news.py tests/test_openbb_scraper.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit the source boundary**

```bash
git add src/infoservice/sources tests/infoservice/sources
git commit -m "feat: add validated source catalog"
```

---

### Task 6: Timezone-aware schedules and idempotent job claiming

**Files:**
- Create: `src/infoservice/scheduling/calculator.py`
- Create: `src/infoservice/scheduling/__init__.py`
- Create: `src/infoservice/scheduling/repository.py`
- Create: `tests/infoservice/scheduling/test_calculator.py`
- Create: `tests/infoservice/scheduling/test_claiming.py`

**Interfaces:**
- Produces: `ScheduleSpec(kind, value, timezone)` and `next_occurrence(spec, after_utc) -> datetime`.
- Produces: `SchedulerRepository.enqueue_due(now, limit) -> list[UUID]`, `RunRepository.claim_next(worker_id, now) -> ClaimedRun | None`, `recover_stale(now, timeout) -> int`.

- [ ] **Step 1: Write failing schedule and DST tests**

```python
def test_daily_moscow_schedule_returns_utc():
    spec = ScheduleSpec(kind="daily", value="09:00", timezone="Europe/Moscow")
    assert next_occurrence(spec, dt("2026-07-20T05:00:00Z")) == dt("2026-07-20T06:00:00Z")


def test_cron_rejects_more_than_hourly():
    with pytest.raises(ScheduleValidationError):
        ScheduleSpec(kind="cron", value="*/15 * * * *", timezone="UTC")
```

- [ ] **Step 2: Write a failing concurrent claim test**

```python
async def test_two_claimers_receive_different_runs(run_repo, queued_runs):
    first, second = await asyncio.gather(
        run_repo.claim_next("worker-a", utcnow()),
        run_repo.claim_next("worker-b", utcnow()),
    )
    assert first.id != second.id
```

- [ ] **Step 3: Verify focused failures**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/scheduling -q`

Expected: scheduling modules do not exist.

- [ ] **Step 4: Implement schedule calculation**

Use `zoneinfo.ZoneInfo` and croniter. Presets compile to cron: daily `M H * * *`, weekdays `M H * * 1-5`, weekly `M H * * D`. Validate by computing successive occurrences for 48 hours and reject any gap under 60 minutes. Convert results to UTC; nonexistent DST wall times move to the first valid minute and ambiguous times choose the first occurrence.

- [ ] **Step 5: Implement PostgreSQL claims**

Inside `async_sessionmaker.begin()`, select due reports and queued runs with `.with_for_update(skip_locked=True)`. Enqueue one missed occurrence per report after downtime, advance `next_run_at` past `now`, and rely on `uq_report_runs_schedule` for idempotency. Mark claims with `worker_id`, `started_at`, status `running`; stale recovery increments `attempt_count` and requeues only while `< 2`, otherwise fails safely.

- [ ] **Step 6: Run schedule and claim tests**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/scheduling -q`

Expected: all scheduling tests pass, including DST and concurrent claims.

- [ ] **Step 7: Commit scheduling primitives**

```bash
git add src/infoservice/scheduling tests/infoservice/scheduling
git commit -m "feat: add durable report scheduling"
```

---

### Task 7: Reusable Horizon execution API and custom instructions

**Files:**
- Create: `src/infoservice/execution/contracts.py`
- Create: `src/infoservice/execution/__init__.py`
- Create: `src/infoservice/execution/horizon.py`
- Modify: `src/orchestrator.py`
- Modify: `src/ai/prompts.py`
- Modify: `src/ai/analyzer.py`
- Modify: `src/ai/summarizer.py`
- Create: `tests/infoservice/execution/test_horizon.py`
- Modify: `tests/test_analyzer.py`
- Modify: `tests/test_summarizer.py`

**Interfaces:**
- Produces: `ReportExecutionRequest(report_id, config, api_key, custom_instruction, lookback_hours)`.
- Produces: `ReportExecutionResult(markdown, items, all_items_count, fetch_report, usage)`.
- Produces: `HorizonReportExecutor.execute(request) -> ReportExecutionResult`.

- [ ] **Step 1: Write failing adapter tests**

```python
async def test_executor_returns_data_without_file_delivery(executor, request, tmp_path):
    result = await executor.execute(request)
    assert result.markdown.startswith("#")
    assert result.all_items_count == 2
    assert not list(tmp_path.rglob("*.md"))


def test_custom_instruction_is_delimited():
    prompt = build_analysis_prompt("Prefer engineering details", "untrusted article")
    assert "<custom_rule>Prefer engineering details</custom_rule>" in prompt
    assert "<source_content>untrusted article</source_content>" in prompt
```

- [ ] **Step 2: Verify the tests fail**

Run: `uv run pytest tests/infoservice/execution/test_horizon.py tests/test_analyzer.py tests/test_summarizer.py -q`

Expected: execution contracts and delimited prompt support are missing.

- [ ] **Step 3: Extract a side-effect-free pipeline method**

Add `HorizonOrchestrator.execute(force_hours=None, custom_instruction=None) -> HorizonRunResult` containing fetch, merge, analyze, filter, enrich and summary generation. Existing `run()` calls `execute()` and then performs legacy file/email/webhook delivery, preserving its output and tests.

`HorizonRunResult` contains `summaries: dict[str, str]`, `important_items`, `all_items_count`, `fetch_report`, and token usage. Empty content returns an empty generated summary rather than exiting the worker without a result.

- [ ] **Step 4: Implement the InfoService adapter**

Map database source records through `SourceCatalog` into `SourcesConfig`, set `AIConfig(provider="deepseek", model=credential.model, api_key_env="")`, `FilteringConfig`, and disabled legacy delivery. Pass `runtime_api_key=request.api_key`; erase the local reference in `finally` and return only normalized DTOs.

- [ ] **Step 5: Thread custom instructions through safe prompt sections**

The system prompt states that `<source_content>` is untrusted and must never override system/custom rules. Escape literal closing delimiter strings from user/source text. Custom rules may change relevance, style and exclusions only; they cannot request tools, secrets, other users or policy changes.

- [ ] **Step 6: Run adapter and full Horizon regression tests**

Run: `uv run pytest tests/infoservice/execution tests/test_analyzer.py tests/test_summarizer.py tests/test_balanced_digest.py tests/test_fetch_reporting.py -q`

Expected: adapter tests and all touched Horizon tests pass.

- [ ] **Step 7: Commit the execution boundary**

```bash
git add src/infoservice/execution src/orchestrator.py src/ai tests
git commit -m "feat: expose Horizon report execution API"
```

---

### Task 8: Safe Telegram report rendering and delivery

**Files:**
- Create: `src/infoservice/delivery/telegram.py`
- Create: `src/infoservice/delivery/__init__.py`
- Create: `tests/infoservice/delivery/test_telegram.py`

**Interfaces:**
- Produces: `TelegramReportRenderer.render(result, report_name) -> RenderedReport`.
- Produces: `TelegramDelivery.send(chat_id, rendered) -> DeliveryResult`.

- [ ] **Step 1: Write failing rendering tests**

```python
def test_renderer_escapes_and_chunks_on_item_boundaries(renderer, long_result):
    rendered = renderer.render(long_result, "AI <daily>")
    assert all(len(part) <= 3800 for part in rendered.messages)
    assert "&lt;daily&gt;" in rendered.messages[0]
    assert all("https://example.com" in part or part == rendered.messages[0]
               for part in rendered.messages[1:])


async def test_429_uses_retry_after(delivery, bot, rendered):
    bot.send_message.side_effect = [TelegramRetryAfter(method=None, message="rate", retry_after=1), Message()]
    assert (await delivery.send(42, rendered)).status == "sent"
```

- [ ] **Step 2: Verify failures**

Run: `uv run pytest tests/infoservice/delivery/test_telegram.py -q`

Expected: delivery module does not exist.

- [ ] **Step 3: Implement semantic chunking and fallback document**

Render a header and one block per item using aiogram HTML utilities. Pack complete blocks up to 3 800 characters; split an oversized block at paragraph boundaries. When total text exceeds 20 messages, send the first overview plus a `BufferedInputFile` named `report-YYYY-MM-DD.md`.

- [ ] **Step 4: Implement delivery retry policy**

Retry `TelegramRetryAfter` after its declared delay and transient network errors with exponential delays 1/2/4 seconds, maximum three attempts. Treat `TelegramForbiddenError` as permanent, return a safe status and disable no data automatically.

- [ ] **Step 5: Run delivery tests and commit**

Run: `uv run pytest tests/infoservice/delivery/test_telegram.py -q`

Expected: all delivery tests pass.

```bash
git add src/infoservice/delivery tests/infoservice/delivery
git commit -m "feat: add safe Telegram report delivery"
```

---

### Task 9: Bot shell, onboarding and LLM management

**Files:**
- Create: `src/infoservice/bot/app.py`
- Create: `src/infoservice/bot/__init__.py`
- Create: `src/infoservice/bot/handlers/__init__.py`
- Create: `src/infoservice/bot/states.py`
- Create: `src/infoservice/bot/keyboards.py`
- Create: `src/infoservice/bot/messages_ru.py`
- Create: `src/infoservice/bot/middleware.py`
- Create: `src/infoservice/bot/handlers/start.py`
- Create: `src/infoservice/bot/handlers/credentials.py`
- Create: `tests/infoservice/bot/test_onboarding.py`
- Create: `tests/infoservice/bot/test_credentials.py`

**Interfaces:**
- Produces: `create_dispatcher(settings, session_factory) -> Dispatcher`.
- Produces main menu callback ids `reports`, `llm`, `settings`, `help`.
- Consumes credential cipher/verifier and repositories from Tasks 3–4.

- [ ] **Step 1: Write failing handler tests**

```python
async def test_start_creates_user_and_requests_timezone(bot_harness):
    replies = await bot_harness.message("/start", user_id=1001, chat_type="private")
    assert "часовой пояс" in replies.last_text.lower()
    assert await bot_harness.users.by_telegram_id(1001)


async def test_key_message_is_deleted_and_only_ciphertext_persisted(bot_harness):
    await bot_harness.enter_key_flow(user_id=1001)
    event = await bot_harness.message("sk-user-secret", user_id=1001)
    assert event.deleted is True
    stored = await bot_harness.credentials.for_user(1001)
    assert "sk-user-secret" not in stored.encrypted_key


async def test_group_chat_redirects_without_creating_user(bot_harness):
    replies = await bot_harness.message("/start", user_id=1001, chat_type="group")
    assert "личный чат" in replies.last_text.lower()
    assert await bot_harness.users.by_telegram_id(1001) is None
```

- [ ] **Step 2: Verify failures**

Run: `uv run pytest tests/infoservice/bot/test_onboarding.py tests/infoservice/bot/test_credentials.py -q`

Expected: bot package is absent.

- [ ] **Step 3: Build aiogram application boundaries**

Use one root `Dispatcher(storage=MemoryStorage())`, separate routers, `tasks_concurrency_limit=32`, and middleware that injects a fresh `AsyncSession` plus current `User`. Reject non-private chats before FSM handlers. Always call `callback.answer()`.

- [ ] **Step 4: Implement onboarding and credential flows**

Timezone flow offers UTC, Europe/Moscow, Europe/Berlin and a validated IANA text entry. Credential flow deletes the key message in `finally`, verifies DeepSeek, encrypts it, upserts provider `deepseek`, and shows only the mask. Replacement requires confirmation; deletion disables scheduled reports until a new key is added.

- [ ] **Step 5: Run bot tests and commit**

Run: `uv run pytest tests/infoservice/bot/test_onboarding.py tests/infoservice/bot/test_credentials.py -q`

Expected: all onboarding/credential tests pass.

```bash
git add src/infoservice/bot tests/infoservice/bot
git commit -m "feat: add Telegram onboarding and BYOK setup"
```

---

### Task 10: Report, rule and schedule management UI

**Files:**
- Create: `src/infoservice/bot/handlers/reports.py`
- Create: `src/infoservice/bot/handlers/schedules.py`
- Create: `src/infoservice/bot/handlers/rules.py`
- Modify: `src/infoservice/bot/states.py`
- Modify: `src/infoservice/bot/keyboards.py`
- Modify: `src/infoservice/bot/messages_ru.py`
- Create: `tests/infoservice/bot/test_reports.py`
- Create: `tests/infoservice/bot/test_schedules.py`

**Interfaces:**
- Produces callback namespace `report:<action>:<uuid>` and FSM `CreateReport`, `EditRules`, `EditSchedule`.
- Consumes repositories, `ScheduleSpec` and product limits.

- [ ] **Step 1: Write failing report wizard tests**

```python
async def test_report_wizard_commits_only_after_confirmation(bot_harness, user):
    await bot_harness.create_report(name="AI", confirm=False)
    assert await bot_harness.reports.list_owned(user.id) == []
    await bot_harness.press("confirm_report")
    assert [r.name for r in await bot_harness.reports.list_owned(user.id)] == ["AI"]


async def test_foreign_report_callback_is_hidden(bot_harness, foreign_report):
    response = await bot_harness.callback(f"report:view:{foreign_report.id}", user_id=1001)
    assert response.alert == "Отчёт не найден"
```

- [ ] **Step 2: Write failing rules and schedule tests**

Test threshold boundaries 0/10, max-items 1/30, prompt 2 000/2 001, report language `ru`/`en`, lookback, cron validation, pause/resume, delete confirmation, manual-run cooldown, last-20 history rendering and re-sending a stored result.

- [ ] **Step 3: Verify failures**

Run: `uv run pytest tests/infoservice/bot/test_reports.py tests/infoservice/bot/test_schedules.py -q`

Expected: report handlers are absent.

- [ ] **Step 4: Implement transactional report wizard and CRUD**

Keep wizard draft in FSM as a Pydantic `ReportDraft`; create the report only on confirmation. Every callback parses UUID safely and calls `get_owned`. Deleting a report requires a second button and cascades sources/runs. Pausing clears no history; resuming recomputes `next_run_at` from current UTC.

- [ ] **Step 5: Implement rules, presets, cron and history UI**

Rules screen shows current threshold, categories, exclusions, item limit, report language, lookback and custom instruction. Schedule screen produces `ScheduleSpec`; manual run creates `ReportRun(trigger="manual", scheduled_for=now)` only when credential exists and cooldown/concurrency checks pass. History offers re-send only for a completed owned run whose stored Markdown has not expired.

- [ ] **Step 6: Run report UI tests and commit**

Run: `uv run pytest tests/infoservice/bot/test_reports.py tests/infoservice/bot/test_schedules.py -q`

Expected: all report UI tests pass.

```bash
git add src/infoservice/bot tests/infoservice/bot
git commit -m "feat: add report rules and schedules UI"
```

---

### Task 11: Source management UI for the complete catalog

**Files:**
- Create: `src/infoservice/bot/handlers/sources.py`
- Modify: `src/infoservice/bot/states.py`
- Modify: `src/infoservice/bot/keyboards.py`
- Modify: `src/infoservice/bot/messages_ru.py`
- Create: `tests/infoservice/bot/test_sources.py`

**Interfaces:**
- Produces callback namespace `source:<action>:<uuid>` and catalog-driven source forms.
- Consumes `SourceCatalog.validate` and report/source ownership repositories.

- [ ] **Step 1: Write failing source-flow tests**

```python
@pytest.mark.parametrize("source_type", ["rss", "telegram", "hackernews", "github"])
async def test_stable_source_can_be_added(bot_harness, report, source_type):
    await bot_harness.add_source(report, source_type, valid_payload(source_type))
    assert source_type in {s.type for s in await bot_harness.sources.list(report.id)}


async def test_disabled_optional_source_is_not_offered(bot_harness):
    labels = await bot_harness.open_source_catalog()
    assert "Twitter / X" not in labels
    assert "OpenBB" not in labels
```

- [ ] **Step 2: Verify failures**

Run: `uv run pytest tests/infoservice/bot/test_sources.py -q`

Expected: source handler is absent.

- [ ] **Step 3: Implement catalog-driven menus and forms**

Render stable, beta and optional sections from `SourceCapability`; beta labels include `β`. Implement explicit FSM form handlers for all ten Horizon source types, but delegate normalization/validation to the catalog. Show capability prerequisites before any optional form. Support list, enable/disable, edit and confirmed delete.

- [ ] **Step 4: Enforce ownership and source count atomically**

Load the parent report with `user_id`, lock it, count sources, validate JSON, then insert. A guessed source/report UUID returns the same `Отчёт не найден`/`Источник не найден` response without revealing ownership.

- [ ] **Step 5: Run source UI tests and commit**

Run: `uv run pytest tests/infoservice/bot/test_sources.py tests/infoservice/sources -q`

Expected: all catalog and handler tests pass.

```bash
git add src/infoservice/bot tests/infoservice/bot
git commit -m "feat: add Telegram source management"
```

---

### Task 12: Scheduler and worker services

**Files:**
- Create: `src/infoservice/scheduling/service.py`
- Create: `src/infoservice/execution/worker.py`
- Create: `src/infoservice/execution/service.py`
- Create: `tests/infoservice/execution/test_worker.py`
- Create: `tests/infoservice/scheduling/test_service.py`

**Interfaces:**
- Produces: `run_scheduler(settings, stop_event) -> None` and `run_worker(settings, bot, stop_event) -> None`.
- Consumes run claims, credential decryption, Horizon executor and Telegram delivery.

- [ ] **Step 1: Write failing lifecycle tests**

```python
async def test_worker_records_partial_result_and_delivers(worker, partial_execution):
    await worker.run_once()
    run = await worker.runs.get(partial_execution.run_id)
    assert run.status == "partial"
    assert run.finished_at is not None
    worker.delivery.send.assert_awaited_once()


async def test_invalid_key_fails_without_retry(worker, invalid_key_execution):
    await worker.run_once()
    run = await worker.runs.get(invalid_key_execution.run_id)
    assert run.status == "failed"
    assert run.attempt_count == 1
    assert "sk-" not in (run.error_summary or "")
```

- [ ] **Step 2: Verify failures**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/execution/test_worker.py tests/infoservice/scheduling/test_service.py -q`

Expected: service loops do not exist.

- [ ] **Step 3: Implement one-run orchestration**

`ExecutionService.run_once()` claims a run, loads report/source/credential using the run's trusted report relation, decrypts into a local variable, executes Horizon, stores final Markdown/counters/source results, commits, then delivers. Status is `partial` when at least one source failed and at least one succeeded. Use `finally` to drop plaintext references and release the in-process semaphore.

Classify auth/validation as permanent; retry network, 429 and 5xx up to three attempts with 1/2/4-second backoff. Store exception class plus redacted message capped at 1 000 characters.

Emit one structured log event per lifecycle transition with run/report ids, duration, item counts, token usage, per-source status and delivery status. Do not log source bodies, generated Markdown, API keys or Telegram message contents.

- [ ] **Step 4: Implement scheduler/worker loops and graceful shutdown**

Scheduler enqueues due reports, recovers stale runs and performs daily retention. Worker creates `worker_concurrency` tasks, sleeps one second when no job exists and stops claiming after SIGTERM while allowing active tasks up to 30 seconds to finish.

- [ ] **Step 5: Run lifecycle and concurrency tests**

Run: `TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice/execution tests/infoservice/scheduling -q`

Expected: status transitions, retries, redaction, duplicate prevention and shutdown tests pass.

- [ ] **Step 6: Commit services**

```bash
git add src/infoservice/execution src/infoservice/scheduling tests/infoservice/execution tests/infoservice/scheduling
git commit -m "feat: run scheduled reports durably"
```

---

### Task 13: Deployment, CI, documentation and acceptance verification

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `README.md`
- Create: `README_RU.md`
- Create: `.github/workflows/test.yml`
- Create: `scripts/healthcheck.py`
- Create: `tests/infoservice/test_acceptance.py`

**Interfaces:**
- Produces Docker services `migrate`, `bot`, `scheduler`, `worker`, `postgres` and healthchecks.
- Produces operator contract documented through `.env.example` and README.

- [ ] **Step 1: Write an acceptance test covering two isolated users**

```python
async def test_two_users_receive_only_their_reports(app_harness):
    alice = await app_harness.onboard(1001, "sk-alice")
    bob = await app_harness.onboard(2002, "sk-bob")
    alice_report = await app_harness.create_rss_report(alice, "09:00")
    await app_harness.run_due(alice_report)
    assert app_harness.messages.for_chat(alice.chat_id)
    assert not app_harness.messages.for_chat(bob.chat_id)
    assert "sk-alice" not in app_harness.logs.text
```

- [ ] **Step 2: Update container layout**

Build two Docker targets: `runtime` with default dependencies and `runtime-full` with `twitter` and `openbb` extras. Compose chooses `${APP_IMAGE_TARGET:-runtime}` for all application processes; an operator enables optional sources by setting `APP_IMAGE_TARGET=runtime-full` together with the capability flags and rebuilding. Compose starts PostgreSQL with a named volume and healthcheck, runs `migrate` to completion, then starts bot/scheduler/worker only after migration succeeds. Mount no writable source tree in production.

- [ ] **Step 3: Add safe environment template and healthcheck**

`.env.example` names `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `APP_ENCRYPTION_KEY`, capability flags, limits and optional `APIFY_TOKEN`, with obvious non-secret placeholders. `scripts/healthcheck.py` checks DB connectivity and process-specific heartbeat rows without printing credentials.

- [ ] **Step 4: Add GitHub Actions with PostgreSQL**

Workflow uses Python 3.11, `astral-sh/setup-uv`, PostgreSQL 16 service, `uv sync --extra dev`, `alembic upgrade head`, focused InfoService tests and the complete Horizon suite. It never runs external Telegram/DeepSeek calls.

- [ ] **Step 5: Rewrite public documentation**

README describes InfoService first, attributes Horizon, links MIT license, lists stable/beta/optional sources, explains BotFather and DeepSeek setup, key-security limits, Docker Compose deployment, backup/restore, update from upstream and removal of user credentials. `README_RU.md` is the complete Russian operator/user guide; English README contains a Russian link.

- [ ] **Step 6: Run migrations, acceptance and the full suite**

Run:

```bash
docker compose -f docker-compose.test.yml up -d postgres
DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+asyncpg://infoservice:infoservice@localhost:55432/infoservice_test uv run pytest tests/infoservice -q
uv run pytest -q
docker compose config --quiet
```

Expected: all InfoService tests pass, the complete Horizon regression suite passes, and Compose validation exits 0.

- [ ] **Step 7: Perform a secret and placeholder scan**

Run:

```bash
rg -n "sk-[A-Za-z0-9]|TELEGRAM_BOT_TOKEN=.+|APP_ENCRYPTION_KEY=.+" . --glob '!uv.lock' --glob '!.git/**'
rg -n "TB[D]|TO[D]O|FIXM[E]|XX[X]" src/infoservice tests/infoservice README.md README_RU.md
```

Expected: first command finds only clearly fake test fixtures; second command prints no production placeholders.

- [ ] **Step 8: Commit deployment and documentation**

```bash
git add Dockerfile docker-compose.yml .env.example README.md README_RU.md .github scripts/healthcheck.py tests/infoservice/test_acceptance.py
git commit -m "docs: ship InfoService deployment and operations"
```

- [ ] **Step 9: Final verification and release candidate tag**

Run:

```bash
git status --short
git log --oneline --decorate -15
uv run pytest -q
```

Expected: working tree is clean, all planned commits are present and the full suite passes. After review, create annotated tag `v0.1.0-rc1`; do not deploy a shared production bot or enable platform-funded LLM access in v1.
