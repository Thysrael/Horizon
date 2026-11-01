"""Load processing profiles from JSON and Markdown files."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from ..models import DigestConfig

BUILTIN_PROFILES_DIR = Path(__file__).resolve().parents[1] / "_builtin_profiles"


class ProfileContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_max_chars: int = Field(default=1000, ge=500, le=100_000)
    enrichment_max_chars: int = Field(default=8000, ge=500, le=100_000)
    sampling: Literal["prefix", "head-middle-tail"] = "prefix"


class ProfileBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    type: Literal["section"] = "section"
    tools: list[str] = Field(default_factory=list)
    optional: bool = False
    primary: bool = False


class ProfileEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    blocks: list[ProfileBlock] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_block_ids(self) -> "ProfileEnrichment":
        ids = [block.id for block in self.blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("enrichment block IDs must be unique")
        primary_blocks = [block for block in self.blocks if block.primary]
        if len(primary_blocks) > 1:
            raise ValueError("enrichment may define at most one primary block")
        if primary_blocks and primary_blocks[0].optional:
            raise ValueError("the primary enrichment block must be required")
        return self


class ProfileDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    name: str
    display_names: dict[str, str] = Field(default_factory=dict)
    match: str
    analysis: str
    content: ProfileContent = Field(default_factory=ProfileContent)
    enrichment: ProfileEnrichment


@dataclass(frozen=True)
class LoadedProfile:
    definition: ProfileDefinition
    match_prompt: str
    analysis_prompt: str
    enrichment_prompt: str

    @property
    def id(self) -> str:
        return self.definition.id


class ProfileRegistry:
    """Validated profiles indexed by ID."""

    def __init__(self, profiles: dict[str, LoadedProfile], default_profile: str):
        if default_profile not in profiles:
            raise ValueError(f"Default profile does not exist: {default_profile}")
        self._profiles = profiles
        self.default_profile = default_profile

    @classmethod
    def load(
        cls,
        profiles_dir: Path,
        default_profile: str,
        *,
        base_dir: Optional[Path] = None,
    ) -> "ProfileRegistry":
        if profiles_dir.is_absolute():
            root = profiles_dir.resolve()
        else:
            root = ((base_dir or Path.cwd()) / profiles_dir).resolve()
            if (
                profiles_dir == Path("profiles")
                and not root.is_dir()
                and BUILTIN_PROFILES_DIR.is_dir()
            ):
                root = BUILTIN_PROFILES_DIR
        profiles: dict[str, LoadedProfile] = {}
        for config_path in sorted(root.glob("*/profile.json")):
            definition = ProfileDefinition.model_validate_json(
                config_path.read_text(encoding="utf-8")
            )
            if definition.id in profiles:
                raise ValueError(f"Duplicate profile ID: {definition.id}")
            profile_dir = config_path.parent.resolve()
            profiles[definition.id] = LoadedProfile(
                definition=definition,
                match_prompt=cls._read_prompt(profile_dir, definition.match),
                analysis_prompt=cls._read_prompt(profile_dir, definition.analysis),
                enrichment_prompt=cls._read_prompt(
                    profile_dir, definition.enrichment.prompt
                ),
            )
        if not profiles:
            raise ValueError(f"No profiles found under {root}")
        return cls(profiles, default_profile)

    @staticmethod
    def _read_prompt(profile_dir: Path, relative_path: str) -> str:
        path = (profile_dir / relative_path).resolve()
        if not path.is_relative_to(profile_dir):
            raise ValueError(f"Prompt path escapes profile directory: {relative_path}")
        return path.read_text(encoding="utf-8").strip()

    def get(self, profile_id: str) -> LoadedProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ValueError(f"Unknown processing profile: {profile_id}") from exc

    def validate_source_references(self, value: object) -> None:
        """Reject unknown explicit profile IDs anywhere in source config."""
        if isinstance(value, dict):
            requested = value.get("profile")
            if isinstance(requested, str):
                normalized = requested.strip()
                if normalized and normalized != "auto":
                    self.get(normalized)
            elif isinstance(requested, list):
                normalized = [
                    profile_id.strip()
                    for profile_id in requested
                    if isinstance(profile_id, str) and profile_id.strip()
                ]
                if not normalized:
                    raise ValueError("profile candidate list cannot be empty")
                if len(normalized) != len(requested):
                    raise ValueError("profile candidates must be non-empty strings")
                if len(normalized) != len(set(normalized)):
                    raise ValueError("profile candidates must be unique")
                if "auto" in normalized:
                    raise ValueError("profile candidate list cannot contain 'auto'")
                for profile_id in normalized:
                    self.get(profile_id)
            for child in value.values():
                self.validate_source_references(child)
        elif isinstance(value, list):
            for child in value:
                self.validate_source_references(child)

    def validate_digest_references(self, digest: "DigestConfig") -> None:
        """Reject unknown profile IDs in profile-based digest quota groups."""
        if digest.group_by != "profile":
            return
        requested = {
            profile_id
            for group in digest.category_groups.values()
            for profile_id in group.categories
        }
        unknown = requested - self.ids
        if unknown:
            raise ValueError(
                'digest.category_groups contains unknown profiles for group_by "profile" '
                f"({', '.join(sorted(unknown))})"
            )

    @property
    def ids(self) -> set[str]:
        return set(self._profiles)

    @property
    def profiles(self) -> tuple[LoadedProfile, ...]:
        return tuple(self._profiles.values())

    @property
    def names(self) -> dict[str, dict[str, str]]:
        return {
            profile_id: {
                "default": profile.definition.name,
                **profile.definition.display_names,
            }
            for profile_id, profile in self._profiles.items()
        }
