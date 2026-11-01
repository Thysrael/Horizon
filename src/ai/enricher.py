"""Profile-driven content enrichment."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
)
from tenacity import retry, retry_if_exception_type, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from .client import AIClient
from .errors import AIProviderUnavailableError
from .localization import normalize_language
from .prompting.enrichment import (
    MAX_TOOL_REQUESTS,
    artifact_prompt,
    block_prompt,
    item_context,
    tool_planning_prompt,
    tool_results_text,
)
from .utils import gather_ai_tasks, parse_json_response
from ..models import ArtifactSource, ContentArtifact, ContentBlock, ContentItem
from ..processing.profiles import LoadedProfile, ProfileBlock, ProfileRegistry
from ..processing.tools import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)

class ToolRequest(BaseModel):
    block_id: str
    tool: str
    arguments: dict[str, Any]
    purpose: str


class ToolPlan(BaseModel):
    tool_requests: list[ToolRequest] = Field(default_factory=list)


class GeneratedArtifact(BaseModel):
    title: str
    blocks: list[ContentBlock]

    @model_validator(mode="after")
    def validate_non_empty_content(self) -> "GeneratedArtifact":
        if not self.title.strip():
            raise ValueError("title must not be empty")
        for block in self.blocks:
            if not block.title.strip() or not block.content.strip():
                raise ValueError(f"block {block.id} must not be empty")
        return self


class GeneratedBlock(BaseModel):
    title: str = ""
    block: Optional[ContentBlock] = None

    @model_validator(mode="after")
    def validate_non_empty_block(self) -> "GeneratedBlock":
        if self.block and (
            not self.block.title.strip() or not self.block.content.strip()
        ):
            raise ValueError(f"block {self.block.id} must not be empty")
        return self


class GeneratedBlockWithHeader(GeneratedBlock):
    @field_validator("title")
    @classmethod
    def validate_non_empty_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


@dataclass
class EnrichmentBatchResult:
    succeeded_ids: list[str] = field(default_factory=list)
    failures: dict[str, str] = field(default_factory=dict)

    @property
    def succeeded_count(self) -> int:
        return len(self.succeeded_ids)

    @property
    def failed_count(self) -> int:
        return len(self.failures)

    @property
    def failed_ids(self) -> list[str]:
        return list(self.failures)

    @property
    def status(self) -> str:
        if not self.failures:
            return "success"
        if self.succeeded_ids:
            return "partial_failure"
        return "failure"


class ContentEnricher:
    """Generate localized block artifacts with profile-scoped tools."""

    def __init__(
        self,
        ai_client: AIClient,
        profiles: ProfileRegistry,
        languages: list[str],
        console: Optional[Console] = None,
        tools: Optional[ToolRegistry] = None,
        *,
        concurrency: int = 1,
    ):
        self.client = ai_client
        self.profiles = profiles
        self.languages = languages
        self.console = console or Console(stderr=True)
        self.tools = tools or ToolRegistry()
        self.concurrency = max(concurrency, 1)
        self._validate_profile_tools()

    def _validate_profile_tools(self) -> None:
        for profile_id in self.profiles.ids:
            profile = self.profiles.get(profile_id)
            for block in profile.definition.enrichment.blocks:
                unknown = set(block.tools) - self.tools.names
                if unknown:
                    raise ValueError(
                        f"Profile {profile_id} block {block.id} uses unknown tools: "
                        f"{', '.join(sorted(unknown))}"
                    )

    @retry(
        retry=retry_if_exception_type(Exception) & retry_if_not_exception_type(AIProviderUnavailableError),
        stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10), reraise=True,
    )
    async def _complete(self, **kwargs: Any) -> str:
        return await self.client.complete(**kwargs)

    async def _complete_model(
        self,
        model: type[ModelT],
        *,
        system: str,
        user: str,
        error_message: str,
        validator: Optional[Callable[[ModelT], None]] = None,
    ) -> ModelT:
        validation_error: Optional[Exception] = None
        for attempt in range(2):
            request: dict[str, Any] = {
                "system": system,
                "user": user,
                "temperature": 0,
            }
            response = await self._complete(**request)
            parsed = parse_json_response(response)
            try:
                result = model.model_validate(parsed)
                if validator:
                    validator(result)
                return result
            except (ValidationError, ValueError) as exc:
                validation_error = exc
                user += (
                    "\n\nYour previous response did not satisfy the output contract. "
                    f"Validation error: {exc}. Return only a corrected JSON object."
                )
        raise ValueError(error_message) from validation_error

    async def enrich_batch(self, items: list[ContentItem]) -> EnrichmentBatchResult:
        semaphore = asyncio.Semaphore(self.concurrency)

        async def process(
            item: ContentItem, task_id: TaskID
        ) -> tuple[str, Optional[Exception]]:
            async with semaphore:
                try:
                    await self._enrich_item(item)
                except AIProviderUnavailableError:
                    raise
                except Exception as exc:
                    logger.error("Error enriching item %s: %s", item.id, exc)
                    return item.id, exc
                finally:
                    progress.advance(task_id)
            return item.id, None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            transient=True,
            console=self.console,
        ) as progress:
            task_id = progress.add_task("Enriching", total=len(items))
            outcomes = await gather_ai_tasks([process(item, task_id) for item in items])

        return EnrichmentBatchResult(
            succeeded_ids=[item_id for item_id, exc in outcomes if exc is None],
            failures={
                item_id: f"{type(exc).__name__}: {exc}"
                for item_id, exc in outcomes
                if exc is not None
            },
        )

    async def _enrich_item(self, item: ContentItem) -> None:
        if not item.processing or not item.processing.analysis:
            raise ValueError("Item must be analyzed before enrichment")
        profile = self.profiles.get(item.processing.classification.profile)
        for language in self.languages:
            item.processing.artifacts.pop(language, None)
        tool_results = await self._plan_and_execute_tools(item, profile)
        sources = self._sources_from_tool_results(tool_results)

        artifacts = {}
        for language in self.languages:
            generated = await self._generate_artifact(
                item, profile, language, tool_results
            )
            self._expand_request_source_refs(generated.blocks, tool_results)
            self._validate_blocks(generated.blocks, profile, tool_results)
            generated.title = normalize_language(generated.title, language)
            for block in generated.blocks:
                block.title = normalize_language(block.title, language)
                block.content = normalize_language(block.content, language)
            referenced = {
                source_id
                for block in generated.blocks
                for source_id in block.source_refs
            }
            artifacts[language] = ContentArtifact(
                language=language,
                title=generated.title,
                blocks=generated.blocks,
                sources=[source for source in sources.values() if source.id in referenced],
            )
        item.processing.artifacts.update(artifacts)

    @staticmethod
    def _expand_request_source_refs(
        blocks: list[ContentBlock],
        tool_results: list[ToolResult],
    ) -> None:
        """Expand a request-level citation to its concrete result citations."""
        request_sources = {
            (result.block_id, result.request_id): [
                f"{result.request_id}-{index}"
                for index, _ in enumerate(result.results, start=1)
            ]
            for result in tool_results
        }
        for block in blocks:
            expanded = []
            for source_ref in block.source_refs:
                expanded.extend(
                    request_sources.get((block.id, source_ref), [source_ref])
                )
            block.source_refs = list(dict.fromkeys(expanded))

    async def _plan_and_execute_tools(
        self, item: ContentItem, profile: LoadedProfile
    ) -> list[ToolResult]:
        allowed = {
            block.id: set(block.tools)
            for block in profile.definition.enrichment.blocks
        }
        if not any(allowed.values()):
            return []

        plan = await self._complete_model(
            ToolPlan,
            system=tool_planning_prompt(profile.definition.enrichment.blocks),
            user=item_context(item, profile, include_content=True),
            error_message="Invalid enrichment tool plan",
        )

        results = []
        seen = set()
        history_requested = False
        for request in plan.tool_requests[:MAX_TOOL_REQUESTS]:
            if request.block_id not in allowed:
                raise ValueError(f"Tool request targets unknown block: {request.block_id}")
            if request.tool not in allowed[request.block_id]:
                raise ValueError(
                    f"Tool {request.tool} is not allowed for block {request.block_id}"
                )
            if request.tool == "history_search":
                if history_requested:
                    continue
                history_requested = True
            key = (request.block_id, request.tool, json.dumps(request.arguments, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            results.append(
                await self.tools.execute(
                    request_id=f"tool-{len(results) + 1}",
                    block_id=request.block_id,
                    tool=request.tool,
                    arguments=request.arguments,
                    current_item=item,
                )
            )
        return results

    async def _generate_artifact(
        self,
        item: ContentItem,
        profile: LoadedProfile,
        language: str,
        tool_results: list[ToolResult],
    ) -> GeneratedArtifact:
        configured_blocks = profile.definition.enrichment.blocks
        result_block_ids = {result.block_id for result in tool_results}
        base_blocks = [
            block for block in configured_blocks if block.id not in result_block_ids
        ]
        title = ""
        generated_by_id: dict[str, ContentBlock] = {}

        if base_blocks:
            required_base_ids = {
                block.id for block in base_blocks if not block.optional
            }
            allowed_base_ids = {block.id for block in base_blocks}

            def validate_required_blocks(generated: GeneratedArtifact) -> None:
                generated_ids = [block.id for block in generated.blocks]
                unknown = set(generated_ids) - allowed_base_ids
                if unknown:
                    raise ValueError(
                        "unknown blocks: " + ", ".join(sorted(unknown))
                    )
                if len(generated_ids) != len(set(generated_ids)):
                    raise ValueError("duplicate block IDs")
                missing = required_base_ids - set(generated_ids)
                if missing:
                    raise ValueError(
                        "missing required blocks: " + ", ".join(sorted(missing))
                    )

            generated = await self._complete_model(
                GeneratedArtifact,
                system=artifact_prompt(profile, language, base_blocks),
                user=(
                    item_context(item, profile, include_content=True)
                    + "\n\n# Tool results\n\nNo tool results are available to these blocks."
                ),
                error_message="Invalid enrichment artifact",
                validator=validate_required_blocks,
            )
            title = generated.title.strip()
            allowed_ids = {block.id for block in base_blocks}
            configured_ids = {block.id for block in configured_blocks}
            for generated_block in generated.blocks:
                if generated_block.id not in allowed_ids:
                    if generated_block.id in configured_ids:
                        continue
                    raise ValueError(
                        f"Artifact contains unknown block: {generated_block.id}"
                    )
                if generated_block.id in generated_by_id:
                    raise ValueError(
                        f"Artifact contains duplicate block: {generated_block.id}"
                    )
                generated_by_id[generated_block.id] = generated_block
            missing = {
                block.id
                for block in base_blocks
                if not block.optional and block.id not in generated_by_id
            }
            if missing:
                raise ValueError(
                    f"Artifact is missing required blocks: {', '.join(sorted(missing))}"
                )

        for block in configured_blocks:
            if block.id not in result_block_ids:
                continue
            block_results = [
                result for result in tool_results if result.block_id == block.id
            ]
            response_model = GeneratedBlockWithHeader if not title else GeneratedBlock

            def validate_requested_block(generated: GeneratedBlock) -> None:
                if generated.block is None:
                    if not block.optional:
                        raise ValueError(f"missing required block: {block.id}")
                    return
                if generated.block.id != block.id:
                    raise ValueError(
                        f"block ID {generated.block.id} does not match {block.id}"
                    )

            generated = await self._complete_model(
                response_model,
                system=block_prompt(
                    profile,
                    language,
                    block,
                    include_header=not title,
                ),
                user=(
                    item_context(item, profile, include_content=True)
                    + f"\n\n# Tool results for block `{block.id}`\n\n"
                    + tool_results_text(block_results)
                ),
                error_message=f"Invalid enrichment block: {block.id}",
                validator=validate_requested_block,
            )

            if not title:
                title = generated.title.strip()
            if generated.block is None:
                if not block.optional:
                    raise ValueError(f"Artifact is missing required block: {block.id}")
                continue
            if generated.block.id != block.id:
                raise ValueError(
                    f"Artifact block {generated.block.id} does not match requested block {block.id}"
                )
            generated_by_id[block.id] = generated.block

        if not title:
            raise ValueError("Enrichment artifact title cannot be empty")
        blocks = [
            generated_by_id[block.id]
            for block in configured_blocks
            if block.id in generated_by_id
        ]
        configured_by_id = {block.id: block for block in configured_blocks}
        for generated_block in blocks:
            generated_block.primary = configured_by_id[generated_block.id].primary
        return GeneratedArtifact(title=title, blocks=blocks)

    @staticmethod
    def _sources_from_tool_results(
        results: list[ToolResult],
    ) -> dict[str, ArtifactSource]:
        sources = {}
        for result in results:
            for index, entry in enumerate(result.results, start=1):
                source_id = f"{result.request_id}-{index}"
                sources[source_id] = ArtifactSource(
                    id=source_id,
                    title=entry["title"],
                    url=entry["url"],
                )
        return sources

    @staticmethod
    def _validate_blocks(
        blocks: list[ContentBlock],
        profile: LoadedProfile,
        tool_results: list[ToolResult],
    ) -> None:
        configured: dict[str, ProfileBlock] = {
            block.id: block for block in profile.definition.enrichment.blocks
        }
        seen = set()
        for block in blocks:
            if block.id not in configured:
                raise ValueError(f"Artifact contains unknown block: {block.id}")
            if block.id in seen:
                raise ValueError(f"Artifact contains duplicate block: {block.id}")
            seen.add(block.id)
            if not block.title.strip() or not block.content.strip():
                raise ValueError(f"Artifact block {block.id} cannot be empty")
            block_source_ids = {
                f"{result.request_id}-{index}"
                for result in tool_results
                if result.block_id == block.id
                for index, _ in enumerate(result.results, start=1)
            }
            unknown_refs = set(block.source_refs) - block_source_ids
            if unknown_refs:
                raise ValueError(
                    f"Block {block.id} contains unknown source refs: "
                    f"{', '.join(sorted(unknown_refs))}"
                )
        required = {block.id for block in configured.values() if not block.optional}
        missing = required - seen
        if missing:
            raise ValueError(
                f"Artifact is missing required blocks: {', '.join(sorted(missing))}"
            )
