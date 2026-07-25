"""Shared scoring and filtering semantics."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional

from .models import ContentItem, FilteringConfig


@dataclass(frozen=True)
class ScoreEvaluation:
    """Diagnostic result of applying one filtering policy to one item."""

    passed: Optional[bool]
    aggregate_score: Optional[float]
    matched_criteria: tuple[str, ...] = ()
    failed_criteria: tuple[str, ...] = ()
    error: Optional[str] = None


def aggregate_custom_score(scores: dict[str, float], filter_mode: str) -> float:
    """Return the scalar score retained for legacy sorting and presentation."""

    if filter_mode == "any":
        return max(scores.values())
    if filter_mode == "all":
        return min(scores.values())
    raise ValueError(f"Unsupported filter mode: {filter_mode}")


def evaluate_item_score(
    item: ContentItem,
    filtering: FilteringConfig,
    *,
    threshold_override: float | None = None,
) -> ScoreEvaluation:
    """Evaluate an item's scores without treating malformed data as a low score."""

    if threshold_override is not None:
        if (
            isinstance(threshold_override, bool)
            or not isinstance(threshold_override, (int, float))
            or not isfinite(float(threshold_override))
            or not 0 <= float(threshold_override) <= 10
        ):
            raise ValueError("Score threshold override must be a finite number from 0 to 10")
        threshold_override = float(threshold_override)

    criteria = filtering.score_criteria
    if criteria is None:
        score = item.ai_score
        if score is None:
            return ScoreEvaluation(
                passed=None,
                aggregate_score=None,
                error=item.ai_analysis_error or "Missing legacy AI score",
            )
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(float(score))
            or not 0 <= float(score) <= 10
        ):
            return ScoreEvaluation(
                passed=None,
                aggregate_score=None,
                error=f"Invalid legacy AI score for item {item.id}",
            )

        numeric_score = float(score)
        threshold = (
            filtering.ai_score_threshold
            if threshold_override is None
            else threshold_override
        )
        return ScoreEvaluation(
            passed=numeric_score >= threshold,
            aggregate_score=numeric_score,
        )

    expected_names = [criterion.name for criterion in criteria]
    expected = set(expected_names)
    actual = set(item.ai_scores)
    missing = [name for name in expected_names if name not in actual]
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing criteria: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected criteria: {', '.join(unexpected)}")
        return ScoreEvaluation(
            passed=None,
            aggregate_score=None,
            error="Invalid custom score set (" + "; ".join(details) + ")",
        )

    scores: dict[str, float] = {}
    for name in expected_names:
        value = item.ai_scores[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(float(value))
            or not 0 <= float(value) <= 10
        ):
            return ScoreEvaluation(
                passed=None,
                aggregate_score=None,
                error=f"Invalid score for criterion '{name}'",
            )
        scores[name] = float(value)

    matched = []
    failed = []
    for criterion in criteria:
        threshold = (
            criterion.threshold
            if threshold_override is None
            else threshold_override
        )
        if scores[criterion.name] >= threshold:
            matched.append(criterion.name)
        else:
            failed.append(criterion.name)

    passed = bool(matched) if filtering.filter_mode == "any" else not failed
    return ScoreEvaluation(
        passed=passed,
        aggregate_score=aggregate_custom_score(scores, filtering.filter_mode),
        matched_criteria=tuple(matched),
        failed_criteria=tuple(failed),
    )
