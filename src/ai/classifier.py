"""Resolve processing profiles for fetched content."""

import logging

from pydantic import BaseModel, Field, ValidationError

from .client import AIClient
from .errors import AIProviderUnavailableError
from .prompting.classification import (
    classification_system_prompt,
    classification_user_prompt,
)
from .utils import parse_json_response
from ..models import ClassificationResult, ContentItem, ProcessingResult
from ..processing.profiles import LoadedProfile, ProfileRegistry

logger = logging.getLogger(__name__)


class ClassificationResponse(BaseModel):
    profile: str
    confidence: float = Field(ge=0, le=1)
    reason: str


class ContentClassifier:
    """Choose a profile from explicit source configuration or AI matching."""

    def __init__(self, client: AIClient, profiles: ProfileRegistry):
        self.client = client
        self.profiles = profiles

    async def resolve(self, item: ContentItem) -> LoadedProfile:
        requested = item.profile or "auto"
        candidate_ids = (
            self._candidate_ids(requested) if isinstance(requested, list) else None
        )
        requested_id = requested.strip() if isinstance(requested, str) else None
        if (
            item.processing
            and item.processing.classification.method == "ai_match"
            and (
                requested_id == "auto"
                or requested_id == item.processing.classification.profile
                or (
                    candidate_ids is not None
                    and item.processing.classification.profile in candidate_ids
                )
            )
        ):
            return self.profiles.get(item.processing.classification.profile)
        if requested_id and requested_id != "auto":
            profile = self.profiles.get(requested_id)
            classification = ClassificationResult(
                profile=profile.id,
                method="source_override",
            )
            if item.processing is None:
                item.processing = ProcessingResult(classification=classification)
            else:
                profile_changed = item.processing.classification.profile != profile.id
                item.processing.classification = classification
                if profile_changed:
                    item.processing.analysis = None
                    item.processing.artifacts.clear()
            return profile

        try:
            result = await self._classify(item, candidate_ids)
            profile = self.profiles.get(result.profile)
            classification = ClassificationResult(
                profile=profile.id,
                method="ai_match",
                confidence=result.confidence,
                reason=result.reason,
            )
        except AIProviderUnavailableError:
            raise
        except Exception as exc:
            fallback_id = (
                self.profiles.default_profile
                if candidate_ids is None
                or self.profiles.default_profile in candidate_ids
                else candidate_ids[0]
            )
            logger.warning(
                "Could not classify %s; using %s: %s",
                item.id,
                fallback_id,
                exc,
            )
            profile = self.profiles.get(fallback_id)
            classification = ClassificationResult(
                profile=profile.id,
                method="ai_match",
                confidence=0,
                reason=f"Classification failed; used fallback profile {profile.id}: {exc}",
            )

        item.processing = ProcessingResult(classification=classification)
        return profile

    def _candidate_ids(self, requested: list[str]) -> tuple[str, ...]:
        candidate_ids = tuple(profile_id.strip() for profile_id in requested)
        if not candidate_ids:
            raise ValueError("profile candidate list cannot be empty")
        if any(not profile_id for profile_id in candidate_ids):
            raise ValueError("profile candidates must be non-empty strings")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("profile candidates must be unique")
        for profile_id in candidate_ids:
            if profile_id == "auto":
                raise ValueError("profile candidate list cannot contain 'auto'")
            self.profiles.get(profile_id)
        return candidate_ids

    async def _classify(
        self,
        item: ContentItem,
        candidate_ids: tuple[str, ...] | None = None,
    ) -> ClassificationResponse:
        response = await self.client.complete(
            system=classification_system_prompt(),
            user=classification_user_prompt(item, self.profiles, candidate_ids),
        )
        parsed = parse_json_response(response)
        if not isinstance(parsed, dict):
            raise ValueError("classifier did not return an object")
        try:
            result = ClassificationResponse.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError("invalid classifier response") from exc
        allowed_ids = set(candidate_ids) if candidate_ids is not None else self.profiles.ids
        if result.profile not in allowed_ids:
            raise ValueError(
                f"classifier selected profile outside the allowed catalog: {result.profile}"
            )
        return result
