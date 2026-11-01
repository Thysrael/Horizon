"""Content analysis using AI."""

import asyncio
import logging
from typing import List, Optional
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn
from tenacity import retry, retry_if_exception_type, retry_if_not_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

from .client import AIClient
from .classifier import ContentClassifier
from .prompting.analysis import analysis_system_prompt, analysis_user_prompt
from .utils import gather_ai_tasks, parse_json_response
from .errors import AIProviderUnavailableError
from ..models import ContentAnalysis, ContentItem
from ..processing.content import select_content, split_content
from ..processing.profiles import ProfileRegistry


class ContentAnalyzer:
    """Analyzes content items using AI to determine importance."""

    def __init__(
        self,
        ai_client: AIClient,
        profiles: ProfileRegistry,
        console: Optional[Console] = None,
        *,
        concurrency: int = 1,
        throttle_sec: float = 0.0,
    ):
        self.client = ai_client
        self.profiles = profiles
        self.classifier = ContentClassifier(ai_client, profiles)
        self.console = console or Console(stderr=True)
        self.concurrency = max(concurrency, 1)
        self.throttle_sec = max(throttle_sec, 0.0)

    @staticmethod
    def _parse_json_response(response: str) -> Optional[dict]:
        """Try multiple strategies to extract a JSON object from an AI response.

        Returns the parsed dict, or None if all strategies fail.
        """
        return parse_json_response(response)

    async def analyze_batch(self, items: List[ContentItem]) -> List[ContentItem]:
        semaphore = asyncio.Semaphore(self.concurrency)

        async def _process(item: ContentItem, index: int, progress_task) -> ContentItem:
            async with semaphore:
                try:
                    await self._analyze_item(item)
                except AIProviderUnavailableError:
                    raise
                except Exception as e:
                    logger.error("Error analyzing item %s: %s", item.id, e)
                    if item.processing:
                        item.processing.analysis = ContentAnalysis(
                            score=None,
                            reason="Analysis failed",
                            summary=item.title,
                        )
                if self.throttle_sec > 0 and index < len(items) - 1:
                    await asyncio.sleep(self.throttle_sec)
            progress.advance(progress_task)
            return item

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task("Analyzing", total=len(items))
            coros = [
                _process(item, i, task) for i, item in enumerate(items)
            ]
            analyzed_items = await gather_ai_tasks(coros)

        return analyzed_items

    @retry(
        retry=retry_if_exception_type(Exception) & retry_if_not_exception_type(AIProviderUnavailableError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=10)
    )
    async def _analyze_item(self, item: ContentItem) -> None:
        """Analyze a single content item.

        Args:
            item: Content item to analyze (modified in-place)
        """
        profile = await self.classifier.resolve(item)
        if item.processing:
            item.processing.artifacts.clear()

        content_parts = split_content(item.content)
        selected_content = select_content(
            content_parts.main,
            profile.definition.content.analysis_max_chars,
            profile.definition.content.sampling,
        )
        content_section = f"Content: {selected_content}" if selected_content else ""

        # Prepare discussion section (comments, engagement)
        discussion_parts = []
        if content_parts.comments:
            discussion_parts.append(
                f"Community Comments:\n{content_parts.comments[:1500]}"
            )

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

        # Generate user prompt
        user_prompt = analysis_user_prompt(item, content_section, discussion_section)

        # Get AI completion
        response = await self.client.complete(
            system=analysis_system_prompt(profile),
            user=user_prompt,
        )

        result, failure = self._validate_analysis_response(response)
        if result is None:
            repair_response = await self.client.complete(
                system=analysis_system_prompt(profile),
                user=(
                    user_prompt
                    + "\n\nYour previous response did not satisfy the output contract "
                    f"({failure}). Analyze the item again and return only the required JSON object."
                ),
                temperature=0,
            )
            result, failure = self._validate_analysis_response(repair_response)

        if result is None:
            logger.warning(
                "Could not parse analysis response for %s after one repair attempt (%s), using defaults",
                item.id,
                failure,
            )
            if item.processing:
                item.processing.analysis = ContentAnalysis(
                    score=None,
                    reason="Analysis response parse failed",
                    summary=item.title,
                )
            return

        if item.processing:
            item.processing.analysis = result

    @classmethod
    def _validate_analysis_response(
        cls,
        response: str,
    ) -> tuple[Optional[ContentAnalysis], str]:
        parsed = cls._parse_json_response(response)
        if not isinstance(parsed, dict):
            return None, "response was not a JSON object"
        try:
            result = ContentAnalysis.model_validate(parsed)
        except ValidationError as exc:
            first_error = exc.errors(include_url=False)[0]
            location = ".".join(str(part) for part in first_error["loc"])
            return None, f"invalid field {location or '<root>'}: {first_error['type']}"
        if result.score is None:
            return None, "score is required by the analysis contract"
        return result, ""
