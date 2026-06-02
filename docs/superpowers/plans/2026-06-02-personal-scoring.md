# Personal Scoring Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional personal scoring preferences to Horizon so AI scoring can be tuned from `data/config.json` without changing code.

**Architecture:** Add a top-level `ScoringConfig` model, render it into a compact scoring-profile prompt section, and pass it explicitly into `ContentAnalyzer` from the main orchestrator and MCP service. Keep the current score output contract unchanged.

**Tech Stack:** Python 3.11, Pydantic v2, pytest, Horizon `StorageManager`, Horizon AI analyzer/orchestrator/MCP service.

---

## File Structure

- Modify `src/models.py`: define `ScoringConfig` and add optional `Config.scoring`.
- Modify `src/ai/analyzer.py`: accept optional scoring config and append it to the analysis system prompt.
- Modify `src/orchestrator.py`: pass `self.config.scoring` to `ContentAnalyzer` for normal analysis and Twitter reply re-analysis.
- Modify `src/mcp/service.py`: pass `ctx.config.scoring` to `ContentAnalyzer` in staged MCP scoring.
- Modify `tests/test_storage.py`: cover config loading with and without `scoring`.
- Modify `tests/test_analyzer.py`: cover prompt rendering and unchanged default prompt behavior.
- Modify `tests/test_mcp_service_smoke.py`: cover MCP scoring constructor wiring with a fake runtime analyzer.
- Modify `data/config.example.json`: add a neutral example scoring block.
- Modify `docs/configuration.md`: document scoring configuration.
- Modify `docs/scoring.md`: document how personal scoring refines the generic rubric.

## Task 1: Add ScoringConfig Model

**Files:**
- Modify: `src/models.py`
- Modify: `tests/test_storage.py`

- [ ] **Step 1: Write failing storage/model test**

Append this test to `tests/test_storage.py`:

```python
def test_load_config_accepts_scoring_profile(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "version": "1.0",
        "ai": {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
        },
        "sources": {"hackernews": {"enabled": True}},
        "filtering": {"ai_score_threshold": 7.0, "time_window_hours": 24},
        "scoring": {
            "profile_name": "personal",
            "primary": ["cognitive value", "paradigm shifts"],
            "secondary": ["engineering usefulness"],
            "boost": ["durable mental models"],
            "downrank": ["generic AI hype"],
            "notes": "Prefer cognitive value first.",
        },
    }), encoding="utf-8")

    storage = StorageManager(data_dir=str(tmp_path))
    config = storage.load_config()

    assert config.scoring is not None
    assert config.scoring.profile_name == "personal"
    assert config.scoring.primary == ["cognitive value", "paradigm shifts"]
    assert config.scoring.secondary == ["engineering usefulness"]
    assert config.scoring.boost == ["durable mental models"]
    assert config.scoring.downrank == ["generic AI hype"]
    assert config.scoring.notes == "Prefer cognitive value first."
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_storage.py::test_load_config_accepts_scoring_profile -q
```

Expected: FAIL because `Config` has no `scoring` field or because extra fields are ignored and `config.scoring` is missing.

- [ ] **Step 3: Add model types**

In `src/models.py`, add this class after `FilteringConfig`:

```python
class ScoringConfig(BaseModel):
    """Optional user preferences that refine AI content scoring."""

    profile_name: str = "default"
    primary: List[str] = Field(default_factory=list)
    secondary: List[str] = Field(default_factory=list)
    boost: List[str] = Field(default_factory=list)
    downrank: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
```

Then update `Config`:

```python
class Config(BaseModel):
    """Main configuration model."""

    version: str = "1.0"
    ai: AIConfig
    sources: SourcesConfig
    filtering: FilteringConfig
    scoring: Optional[ScoringConfig] = None
    email: Optional[EmailConfig] = None
    webhook: Optional[WebhookConfig] = None
```

- [ ] **Step 4: Run storage tests**

Run:

```bash
uv run pytest tests/test_storage.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_storage.py
git commit -m "feat(scoring): add scoring config model" -m "AI: Codex"
```

## Task 2: Add Analyzer Prompt Rendering

**Files:**
- Modify: `src/ai/analyzer.py`
- Modify: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing prompt tests**

Add imports to `tests/test_analyzer.py`:

```python
from src.ai.prompts import CONTENT_ANALYSIS_SYSTEM
from src.models import ScoringConfig
```

Append these tests:

```python
def test_build_system_prompt_without_scoring_uses_base_prompt():
    analyzer = ContentAnalyzer(SimpleNamespace())

    assert analyzer._build_system_prompt() == CONTENT_ANALYSIS_SYSTEM


def test_build_system_prompt_includes_personal_scoring_profile():
    scoring = ScoringConfig(
        profile_name="personal",
        primary=["cognitive value", "paradigm shifts"],
        secondary=["engineering usefulness"],
        boost=["durable mental models"],
        downrank=["generic AI hype"],
        notes="Prefer cognitive value first.",
    )
    analyzer = ContentAnalyzer(SimpleNamespace(), scoring_config=scoring)

    prompt = analyzer._build_system_prompt()

    assert CONTENT_ANALYSIS_SYSTEM in prompt
    assert "Personal scoring profile: personal" in prompt
    assert "Primary high-score signals" in prompt
    assert "- cognitive value" in prompt
    assert "- paradigm shifts" in prompt
    assert "Secondary high-score signals" in prompt
    assert "- engineering usefulness" in prompt
    assert "Boost when content matches" in prompt
    assert "- durable mental models" in prompt
    assert "Downrank when content is" in prompt
    assert "- generic AI hype" in prompt
    assert "Prefer cognitive value first." in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_analyzer.py::test_build_system_prompt_without_scoring_uses_base_prompt tests/test_analyzer.py::test_build_system_prompt_includes_personal_scoring_profile -q
```

Expected: FAIL because `ContentAnalyzer` does not accept `scoring_config` and has no `_build_system_prompt`.

- [ ] **Step 3: Update ContentAnalyzer constructor and prompt builder**

In `src/ai/analyzer.py`, update imports:

```python
from ..models import ContentItem, ScoringConfig
```

Replace the constructor with:

```python
    def __init__(self, ai_client: AIClient, scoring_config: ScoringConfig | None = None):
        self.client = ai_client
        self.scoring_config = scoring_config
```

Add these methods to `ContentAnalyzer`:

```python
    @staticmethod
    def _format_list_section(title: str, values: List[str]) -> str:
        cleaned = [value.strip() for value in values if value and value.strip()]
        if not cleaned:
            return ""
        lines = "\n".join(f"- {value}" for value in cleaned)
        return f"{title}:\n{lines}"

    def _build_system_prompt(self) -> str:
        """Return the analysis prompt, optionally refined by user scoring preferences."""
        scoring = self.scoring_config
        if not scoring:
            return CONTENT_ANALYSIS_SYSTEM

        sections = [
            f"Personal scoring profile: {scoring.profile_name}",
            "Use this profile to refine, not replace, the generic rubric above.",
            "Primary high-score signals should be treated as the strongest reasons to score content 8-10.",
            self._format_list_section("Primary high-score signals", scoring.primary),
            "Secondary high-score signals can raise a good item when quality and relevance are also strong.",
            self._format_list_section("Secondary high-score signals", scoring.secondary),
            self._format_list_section("Boost when content matches", scoring.boost),
            self._format_list_section("Downrank when content is", scoring.downrank),
        ]
        if scoring.notes and scoring.notes.strip():
            sections.append(f"Additional preference notes: {scoring.notes.strip()}")
        sections.append(
            "When these preferences affect the score, mention the matched cognitive or practical signal in the JSON reason field."
        )
        profile_text = "\n\n".join(section for section in sections if section)
        return f"{CONTENT_ANALYSIS_SYSTEM.rstrip()}\n\n{profile_text}\n"
```

- [ ] **Step 4: Use prompt builder in AI call**

In `_analyze_item`, replace:

```python
            system=CONTENT_ANALYSIS_SYSTEM,
```

with:

```python
            system=self._build_system_prompt(),
```

- [ ] **Step 5: Run analyzer tests**

Run:

```bash
uv run pytest tests/test_analyzer.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/ai/analyzer.py tests/test_analyzer.py
git commit -m "feat(scoring): inject scoring profile into analysis prompt" -m "AI: Codex"
```

## Task 3: Wire Scoring Config Through Main and MCP Flows

**Files:**
- Modify: `src/orchestrator.py`
- Modify: `src/mcp/service.py`
- Modify: `tests/test_mcp_service_smoke.py`

- [ ] **Step 1: Update MCP test imports**

In `tests/test_mcp_service_smoke.py`, replace:

```python
from src.mcp.service import HorizonPipelineService
```

with:

```python
from src.mcp.service import HorizonPipelineService, PipelineContext
```

- [ ] **Step 2: Add MCP scoring wiring test**

Append this exact test to `tests/test_mcp_service_smoke.py`:

```python
def test_score_items_passes_scoring_config_to_analyzer(tmp_path, monkeypatch):
    captured = {}

    class FakeAnalyzer:
        def __init__(self, ai_client, scoring_config=None):
            captured["ai_client"] = ai_client
            captured["scoring_config"] = scoring_config

        async def analyze_batch(self, items):
            for item in items:
                item.ai_score = 8.0
            return items

    scoring = SimpleNamespace(profile_name="personal")
    config = SimpleNamespace(
        ai=SimpleNamespace(),
        scoring=scoring,
        filtering=SimpleNamespace(ai_score_threshold=7.0),
    )
    runtime = SimpleNamespace(
        create_ai_client=lambda ai: "client",
        ContentAnalyzer=FakeAnalyzer,
    )

    service = HorizonPipelineService(runs_root=tmp_path / "runs")
    run_id = service.run_store.create_run("test-run")
    service.run_store.save_items(run_id, "raw", [make_item("item-1").model_dump(mode="json")])

    monkeypatch.setattr(
        service,
        "_load_stage_items",
        lambda **kwargs: ([make_item("item-1")], PipelineContext(
            horizon_path=tmp_path,
            config_path=tmp_path / "config.json",
            runtime=runtime,
            config=config,
        )),
    )

    result = asyncio.run(service.score_items(run_id=run_id))

    assert result["scored"] == 1
    assert captured["ai_client"] == "client"
    assert captured["scoring_config"] is scoring
```
- [ ] **Step 3: Run MCP test to verify it fails**

Run:

```bash
uv run pytest tests/test_mcp_service_smoke.py::test_score_items_passes_scoring_config_to_analyzer -q
```

Expected: FAIL because `score_items` currently calls `ContentAnalyzer(ai_client)` without scoring config.

- [ ] **Step 4: Wire orchestrator analysis**

In `src/orchestrator.py`, update `_analyze_content`:

```python
        analyzer = ContentAnalyzer(ai_client, scoring_config=self.config.scoring)
```

Update `_expand_twitter_discussion` re-analysis:

```python
        analyzer = ContentAnalyzer(ai_client, scoring_config=self.config.scoring)
```

- [ ] **Step 5: Wire MCP scoring**

In `src/mcp/service.py`, update `score_items`:

```python
        analyzer = ctx.runtime.ContentAnalyzer(
            ai_client,
            scoring_config=getattr(ctx.config, "scoring", None),
        )
```

- [ ] **Step 6: Run focused MCP and analyzer tests**

Run:

```bash
uv run pytest tests/test_mcp_service_smoke.py::test_score_items_passes_scoring_config_to_analyzer tests/test_analyzer.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/orchestrator.py src/mcp/service.py tests/test_mcp_service_smoke.py
git commit -m "feat(scoring): wire scoring profile through pipelines" -m "AI: Codex"
```

## Task 4: Update Docs and Example Config

**Files:**
- Modify: `data/config.example.json`
- Modify: `docs/configuration.md`
- Modify: `docs/scoring.md`

- [ ] **Step 1: Add neutral scoring example to config example**

In `data/config.example.json`, insert this top-level `scoring` block between the existing `filtering` block and the existing `webhook` block:

```json
  "filtering": {
    "ai_score_threshold": 6.0,
    "time_window_hours": 24
  },
  "scoring": {
    "profile_name": "default",
    "primary": [],
    "secondary": [],
    "boost": [],
    "downrank": [],
    "notes": null
  },
  "webhook": {
```

- [ ] **Step 2: Validate example JSON**

Run:

```bash
uv run python -m json.tool data/config.example.json >/tmp/horizon-config-example.json
```

Expected: command exits 0.

- [ ] **Step 3: Add configuration docs section**

In `docs/configuration.md`, add a section near filtering or AI configuration:

````markdown
## Personal Scoring Profile

Horizon's default scorer uses a generic technical-news rubric. You can optionally add a top-level `scoring` block to refine that rubric toward your own interests without changing the output schema.

```json
{
  "scoring": {
    "profile_name": "personal",
    "primary": [
      "cognitive value",
      "paradigm shifts",
      "transferable insights"
    ],
    "secondary": [
      "engineering usefulness",
      "automation workflows",
      "developer productivity"
    ],
    "boost": [
      "changes how I think about AI, products, engineering, or work",
      "contains durable mental models or decision frameworks",
      "reveals a structural trend or shift",
      "has actionable engineering or automation lessons"
    ],
    "downrank": [
      "generic AI hype",
      "thin product announcements",
      "funding news without technical or strategic signal",
      "tutorials without novelty",
      "engagement without substance"
    ],
    "notes": "Prefer cognitive value first, practical engineering value second."
  }
}
```

- `profile_name`: Human-readable name for the profile.
- `primary`: Strongest signals for 8-10 scores.
- `secondary`: Supporting signals for high scores.
- `boost`: Specific qualities that should raise an item's score.
- `downrank`: Qualities that should lower an item's score.
- `notes`: Free-form preference guidance.

The profile refines the default rubric; it does not replace basic quality checks such as novelty, substance, relevance, and discussion quality.
````

- [ ] **Step 4: Add scoring docs explanation**

In `docs/scoring.md`, add:

```markdown
## Optional Personal Scoring

If `data/config.json` includes a top-level `scoring` block, Horizon appends that profile to the AI scoring prompt. The model still returns the same fields: `score`, `reason`, `summary`, and `tags`.

Personal scoring is useful when your daily brief should optimize for a specific lens, such as cognitive value, product strategy, engineering usefulness, or automation ideas. The `reason` field should mention the preference that affected the score when relevant.
```

- [ ] **Step 5: Run docs/config validation**

Run:

```bash
uv run python -m json.tool data/config.example.json >/tmp/horizon-config-example.json
uv run pytest tests/test_storage.py tests/test_analyzer.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add data/config.example.json docs/configuration.md docs/scoring.md
git commit -m "docs(scoring): document personal scoring config" -m "AI: Codex"
```

## Task 5: Final Verification

**Files:**
- Read only unless verification reveals a bug.

- [ ] **Step 1: Run focused test suite**

Run:

```bash
uv run pytest tests/test_storage.py tests/test_analyzer.py tests/test_mcp_service_smoke.py -q
```

Expected: PASS.

- [ ] **Step 2: Validate example config load through StorageManager**

Run:

```bash
tmpdir="$(mktemp -d)"
cp data/config.example.json "$tmpdir/config.json"
uv run python - <<PY
from src.storage.manager import StorageManager
cfg = StorageManager(data_dir="$tmpdir").load_config()
print("ok", cfg.scoring.profile_name if cfg.scoring else "no-scoring")
PY
```

Expected: prints `ok default`.

- [ ] **Step 3: Inspect git history and status**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected: branch is `feat-personal-scoring`; working tree is clean; recent commits include the design and implementation commits.

- [ ] **Step 4: Summarize for user**

Report:

- Branch name.
- Files changed.
- Test commands and results.
- That no live AI scoring or Apify calls were run.

No commit is needed in this task if the working tree is clean.
