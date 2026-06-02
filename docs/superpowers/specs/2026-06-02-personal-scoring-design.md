# Personal Scoring Configuration Design

## Summary

Horizon currently uses a fixed AI scoring rubric for technical and academic content. This design adds an optional `scoring` configuration block so users can tune scoring toward personal preferences without editing source code.

For the first version, the target profile prioritizes cognitive value first and engineering usefulness second:

- Cognitive value: content that changes judgment frameworks, reveals structural shifts, or creates durable mental models.
- Engineering usefulness: content that improves automation workflows, developer productivity, architecture choices, or practical implementation decisions.

When `scoring` is absent, Horizon keeps the current scoring behavior.

## Goals

- Let users express personal scoring preferences in `data/config.json`.
- Keep the current `ai_score`, `ai_reason`, `ai_summary`, and `ai_tags` output shape.
- Preserve existing configs and example configs through optional fields and defaults.
- Make score reasons explain whether an item matched cognitive or practical value.
- Document the new configuration in both configuration and scoring docs.

## Non-Goals

- Do not add multidimensional score fields such as `cognitive_score` or `practical_score` in the first version.
- Do not change summary rendering, webhook payload shape, or MCP run artifact shape.
- Do not add a UI for editing scoring profiles.
- Do not run live scoring during implementation tests.

## Configuration Shape

Add an optional top-level `scoring` block:

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

All fields except `profile_name` are optional. Empty arrays are allowed and ignored in prompt rendering.

## Data Model

Add `ScoringConfig` to `src/models.py`:

- `profile_name: str = "default"`
- `primary: List[str] = Field(default_factory=list)`
- `secondary: List[str] = Field(default_factory=list)`
- `boost: List[str] = Field(default_factory=list)`
- `downrank: List[str] = Field(default_factory=list)`
- `notes: Optional[str] = None`

Add `scoring: Optional[ScoringConfig] = None` to `Config`.

Using a top-level config keeps this separate from `filtering`, which controls thresholding, and from `ai`, which controls provider behavior.

## Prompt Injection

Keep the existing base `CONTENT_ANALYSIS_SYSTEM` rubric. When `config.scoring` is present, append a compact "Personal scoring profile" section to the system prompt before calling the AI model.

The appended section should:

- State that the configured preferences refine the generic rubric.
- Treat `primary` dimensions as the strongest high-score signal.
- Treat `secondary` dimensions as supporting high-score signals.
- Ask the model to boost matching items and downrank low-signal items.
- Ask the model to mention the matched preference in `reason` when it affects the score.

If no `scoring` profile is configured, send the current prompt unchanged.

## Analyzer Changes

Update `ContentAnalyzer` so it can access scoring config through the AI client config:

- Add `_build_system_prompt()` or equivalent method.
- Read `getattr(self.client.config, "scoring", None)` if the AI client config can carry it, or pass scoring config into `ContentAnalyzer` explicitly.
- Prefer explicit dependency injection if attaching `scoring` to `AIConfig` would blur model-provider settings.

Recommended implementation: pass `scoring_config` into `ContentAnalyzer(ai_client, scoring_config=None)`. `HorizonOrchestrator` and MCP service already hold full `Config`, so they can pass `self.config.scoring`.

## Compatibility

Existing configs without `scoring` must still validate.

Existing AI providers are unaffected because the output JSON contract is unchanged:

```json
{
  "score": 8,
  "reason": "Brief explanation",
  "summary": "One-sentence summary",
  "tags": ["tag"]
}
```

MCP scoring, pipeline runs, enrichment, filtering, summaries, email, and webhook behavior continue to use the existing `ai_score` field.

## Documentation

Update:

- `docs/configuration.md`: add `scoring` block reference and an example personal profile.
- `docs/scoring.md`: explain generic rubric plus optional personal profile refinement.
- `data/config.example.json`: include a neutral `scoring` block that demonstrates the supported fields without encoding the personal cognitive-first profile as the project default.

## Tests

Add focused tests without live AI calls:

- Model validation accepts configs with and without `scoring`.
- Analyzer prompt builder returns the original prompt when scoring config is absent.
- Analyzer prompt builder includes primary, secondary, boost, downrank, and notes when provided.
- Analyzer still parses normal AI JSON output into `ai_score`, `ai_reason`, `ai_summary`, and `ai_tags`.
- MCP scoring path passes scoring config into `ContentAnalyzer` if the implementation uses explicit injection.

## Risks

- Overly long scoring profiles can bloat prompts. Keep rendering concise and preserve truncation of item content.
- Personal preferences may make scores less comparable across users. This is acceptable for local Horizon runs, but global Hub telemetry should treat profiles as context if aggregated later.
- If the model treats personal preferences as absolute rules, it may over-score niche content. The prompt should state that preferences refine, not replace, the generic quality rubric.

## Implementation Decisions

- Keep `data/config.example.json` neutral. Put the cognitive-first personal profile example in docs, not as the repository default.
- Do not update the setup wizard in this iteration. The wizard can support scoring preferences later after the config path is stable.
