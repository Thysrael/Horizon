"""Content analysis using AI."""

import asyncio
from math import isfinite
from typing import List, Optional
from pydantic import BaseModel, ValidationError, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn

from .client import AIClient
from .prompts import build_content_analysis_system, build_content_analysis_user
from .utils import parse_json_response
from ..models import ContentItem, FilteringConfig, ScoreCriterionConfig
from ..scoring import aggregate_custom_score

DEFAULT_THROTTLE_SEC = 0.0


def _validated_score(value: object, *, field_name: str) -> float:
    """Accept only finite JSON numbers in the documented 0-10 range."""

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
        or not 0 <= float(value) <= 10
    ):
        raise ValueError(f"{field_name} must be a finite number from 0 to 10")
    return float(value)


class BaseAnalysisResult(BaseModel):
    """Fields shared by legacy and user-defined analysis responses."""

    reason: str
    summary: str
    tags: list[str]

    @field_validator("reason", "summary", mode="before")
    @classmethod
    def validate_text(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("must be a string")
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, value: object) -> object:
        if not isinstance(value, list) or any(not isinstance(tag, str) for tag in value):
            raise ValueError("tags must be a list of strings")
        return value


class AnalysisResult(BaseAnalysisResult):
    """Validated structured result returned by the legacy analysis prompt."""

    score: float

    @field_validator("score", mode="before")
    @classmethod
    def validate_score(cls, value: object) -> float:
        return _validated_score(value, field_name="score")


class CustomAnalysisResult(BaseAnalysisResult):
    """Validated structured result for user-defined criteria."""

    scores: dict[str, float]

    @field_validator("scores", mode="before")
    @classmethod
    def validate_scores(cls, value: object) -> dict[str, float]:
        if not isinstance(value, dict):
            raise ValueError("scores must be an object")

        result: dict[str, float] = {}
        for name, score in value.items():
            if not isinstance(name, str):
                raise ValueError("score names must be strings")
            result[name] = _validated_score(
                score,
                field_name=f"score '{name}'",
            )
        return result


class ContentAnalyzer:
    """Analyzes content items using AI to determine importance."""

    def __init__(
        self,
        ai_client: AIClient,
        filtering: FilteringConfig | None = None,
    ):
        self.client = ai_client
        self.filtering = filtering

    @property
    def criteria(self) -> list[ScoreCriterionConfig] | None:
        """Return configured criteria, or None for the legacy scoring contract."""

        if self.filtering is None:
            return None
        return self.filtering.score_criteria

    @staticmethod
    def _parse_json_response(response: str) -> Optional[dict]:
        """Try multiple strategies to extract a JSON object from an AI response.

        Returns the parsed dict, or None if all strategies fail.
        """
        return parse_json_response(response)

    def _get_throttle_sec(self) -> float:
        """Return the configured inter-item throttle, clamped to zero or above."""
        config = getattr(self.client, "config", None)
        throttle_sec = getattr(config, "throttle_sec", DEFAULT_THROTTLE_SEC)
        return max(throttle_sec, 0.0)

    def _get_concurrency(self) -> int:
        """Return the configured analysis concurrency, clamped to 1 or above."""
        config = getattr(self.client, "config", None)
        concurrency = getattr(config, "analysis_concurrency", 1)
        return max(concurrency, 1)

    @staticmethod
    def _validation_error_message(error: ValidationError) -> str:
        details = []
        for item in error.errors(include_url=False):
            location = ".".join(str(part) for part in item["loc"]) or "response"
            details.append(f"{location}: {item['msg']}")
        return "; ".join(details)

    @staticmethod
    def _mark_analysis_error(item: ContentItem, message: str) -> None:
        """Leave an item explicitly unscored and retain a safe diagnostic."""

        item.ai_score = None
        item.ai_scores = {}
        item.ai_reason = None
        item.ai_summary = item.title
        item.ai_tags = []
        item.ai_analysis_error = message

    async def analyze_batch(self, items: List[ContentItem]) -> List[ContentItem]:
        throttle_sec = self._get_throttle_sec()
        concurrency = self._get_concurrency()
        semaphore = asyncio.Semaphore(concurrency)

        async def _process(item: ContentItem, index: int, progress_task) -> ContentItem:
            async with semaphore:
                try:
                    await self._analyze_item(item)
                except Exception as e:
                    error_type = type(e).__name__
                    message = f"AI analysis failed after retries ({error_type})"
                    print(f"Error analyzing item {item.id}: {message}")
                    self._mark_analysis_error(item, message)
                if throttle_sec > 0 and index < len(items) - 1:
                    await asyncio.sleep(throttle_sec)
            progress.advance(progress_task)
            return item

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing", total=len(items))
            coros = [
                _process(item, i, task) for i, item in enumerate(items)
            ]
            analyzed_items = await asyncio.gather(*coros)

        return analyzed_items

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=10)
    )
    async def _analyze_item(self, item: ContentItem) -> None:
        """Analyze a single content item.

        Args:
            item: Content item to analyze (modified in-place)
        """
        # Prepare content section
        content_section = ""
        if item.content:
            # Split off comments if present
            content_text = item.content
            if "--- Top Comments ---" in content_text:
                main, comments_part = content_text.split("--- Top Comments ---", 1)
                content_section = f"Content: {main.strip()[:800]}"
            else:
                content_section = f"Content: {content_text[:1000]}"

        # Prepare discussion section (comments, engagement)
        discussion_parts = []
        if item.content and "--- Top Comments ---" in item.content:
            comments_part = item.content.split("--- Top Comments ---", 1)[1]
            discussion_parts.append(f"Community Comments:\n{comments_part[:1500]}")

        meta = item.metadata
        engagement_items = []
        if meta.get("score"):
            engagement_items.append(f"score: {meta['score']}")
        if meta.get("descendants"):
            engagement_items.append(f"{meta['descendants']} comments")
        if meta.get("favorite_count"):
            engagement_items.append(f"{meta['favorite_count']} likes")
        if meta.get("retweet_count"):
            engagement_items.append(f"{meta['retweet_count']} retweets")
        if meta.get("reply_count"):
            engagement_items.append(f"{meta['reply_count']} replies")
        if meta.get("views"):
            engagement_items.append(f"{meta['views']} views")
        if meta.get("bookmarks"):
            engagement_items.append(f"{meta['bookmarks']} bookmarks")
        if meta.get("upvote_ratio"):
            engagement_items.append(f"upvote ratio: {meta['upvote_ratio']:.0%}")
        if engagement_items:
            discussion_parts.append(f"Engagement: {', '.join(engagement_items)}")
        if meta.get("discussion_url"):
            discussion_parts.append(f"Discussion: {meta['discussion_url']}")
        if meta.get("community_note"):
            discussion_parts.append(f"Community Note: {meta['community_note']}")

        discussion_section = "\n".join(discussion_parts) if discussion_parts else ""

        # Generate prompts from either the legacy contract or configured criteria.
        criteria = self.criteria
        system_prompt = build_content_analysis_system(criteria)
        user_prompt = build_content_analysis_user(
            criteria=criteria,
            title=item.title,
            source=f"{item.source_type.value}",
            author=item.author or "Unknown",
            url=str(item.url),
            content_section=content_section,
            discussion_section=discussion_section,
        )

        # Get AI completion
        response = await self.client.complete(
            system=system_prompt,
            user=user_prompt,
        )

        # Parse JSON response without converting malformed output into a low score.
        parsed = self._parse_json_response(response)
        if parsed is None:
            message = "Analysis response was not a valid JSON object"
            print(f"Warning: {message} for {item.id}; item left unscored")
            self._mark_analysis_error(item, message)
            return

        try:
            if criteria is None:
                result = AnalysisResult.model_validate(parsed)
            else:
                result = CustomAnalysisResult.model_validate(parsed)
        except ValidationError as error:
            message = (
                "Analysis response validation failed: "
                + self._validation_error_message(error)
            )
            print(f"Warning: {message} for {item.id}; item left unscored")
            self._mark_analysis_error(item, message)
            return

        if criteria is not None:
            expected_names = [criterion.name for criterion in criteria]
            expected = set(expected_names)
            actual = set(result.scores)
            missing = [name for name in expected_names if name not in actual]
            unexpected = sorted(actual - expected)
            if missing or unexpected:
                details = []
                if missing:
                    details.append(f"missing criteria: {', '.join(missing)}")
                if unexpected:
                    details.append(f"unexpected criteria: {', '.join(unexpected)}")
                message = "Analysis response score keys invalid (" + "; ".join(details) + ")"
                print(f"Warning: {message} for {item.id}; item left unscored")
                self._mark_analysis_error(item, message)
                return

            ordered_scores = {
                name: result.scores[name]
                for name in expected_names
            }
            filter_mode = self.filtering.filter_mode if self.filtering else "any"
            item.ai_scores = ordered_scores
            item.ai_score = aggregate_custom_score(ordered_scores, filter_mode)
        else:
            item.ai_scores = {}
            item.ai_score = result.score

        # Update item with analysis results
        item.ai_reason = result.reason
        item.ai_summary = result.summary
        item.ai_tags = result.tags
        item.ai_analysis_error = None
