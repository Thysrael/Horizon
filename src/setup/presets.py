"""Preset source library loader and keyword matching.

Supports loading from the horizon-site API (preferred) or local file (fallback).
API data is served in horizon-site's own format (Category/SourceType enums)
and transformed internally to the preset format that match_domains() expects.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

from .tag_aliases import get_tag_aliases


API_BASE_URL = os.environ.get(
    "HORIZON_API_URL", "https://horizon1123.top"
)
PRESETS_ENDPOINT = f"{API_BASE_URL}/api/presets"
REQUEST_TIMEOUT = 10  # seconds


def _matches_input_term(term: str, tokens: set, input_lower: str) -> bool:
    """Match a preset term without treating short ASCII tags as substrings."""
    normalized = term.lower()
    if normalized in tokens:
        return True
    if normalized.isascii() and normalized.isalpha() and len(normalized) <= 2:
        return re.search(
            rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])",
            input_lower,
        ) is not None
    return normalized in input_lower


def fetch_presets() -> Optional[Dict]:
    """Fetch presets from the horizon-site API.

    Returns:
        Dict in the internal preset format (with "domains" key),
        or None if the fetch fails.
    """
    try:
        response = httpx.get(
            PRESETS_ENDPOINT,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        if "categories" not in data:
            return None

        return _transform_api_response(data)
    except (httpx.HTTPError, json.JSONDecodeError, ValueError):
        return None


def _transform_api_response(api_data: Dict) -> Dict:
    """Transform horizon-site API response to the internal preset format.

    The API returns data in horizon-site's format (Category enum IDs like
    "AI_ML", SourceType enums like "REDDIT"). This function converts it
    to the preset format with kebab-case IDs and lowercase type strings
    that match_domains() and collect_sources_from_domains() expect.

    Args:
        api_data: Raw API response with "categories" key.

    Returns:
        Dict with "domains" key in preset format.
    """
    domains = []
    for category in api_data.get("categories", []):
        sources = []
        for src in category.get("sources", []):
            config = dict(src.get("config", {}))

            # Horizon-site stores "name" at the source level, but
            # horizon's build_config() expects it inside config for RSS sources.
            src_type = src.get("type", "rss")
            source_name = src.get("name", "")
            if src_type == "rss" and source_name and "name" not in config:
                config["name"] = source_name

            # Remove the internal "subtype" field that horizon-site uses
            # for GitHub sources — horizon uses the type field instead.
            if src_type in ("github_user", "github_repo"):
                config.pop("subtype", None)

            sources.append({
                "type": src_type,
                "description": src.get("description", ""),
                "description_zh": src.get("description_zh", src.get("description", "")),
                "tags": src.get("tags", []),
                "config": config,
            })

        domains.append({
            "id": category.get("id", "").lower().replace("_", "-"),
            "name": category.get("name", ""),
            "name_zh": category.get("name_zh", category.get("name", "")),
            "keywords": category.get("keywords", []),
            "sources": sources,
        })

    return {"domains": domains}


def load_presets(
    presets_path: str = "data/presets.json",
    prefer_api: bool = True,
) -> Dict:
    """Load presets from API (preferred) or local file (fallback).

    Args:
        presets_path: Path to the local presets JSON file for fallback.
        prefer_api: Whether to try the API first. Set False for offline mode
            or when HORIZON_OFFLINE environment variable is set.

    Returns:
        Dict with "domains" key containing preset data.

    Raises:
        FileNotFoundError: If both API and local file are unavailable.
    """
    offline = os.environ.get("HORIZON_OFFLINE", "").lower() in ("1", "true", "yes")

    if prefer_api and not offline:
        api_presets = fetch_presets()
        if api_presets is not None:
            return api_presets

    path = Path(presets_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Presets file not found: {path}\n"
            f"API fetch also failed. Please check your connection "
            f"or ensure {presets_path} exists."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def match_domains(
    user_input: str,
    presets: Dict,
    threshold: float = 0.1,
) -> List[Tuple[Dict, float]]:
    """Match user interest description against preset domains.

    Performs case-insensitive keyword matching against domain keywords and
    source tags. Returns matched domains sorted by relevance score.

    Args:
        user_input: Free-form user interest description (supports mixed languages).
        presets: Loaded presets dictionary.
        threshold: Minimum score (0–1) to include a domain.

    Returns:
        List of (domain_dict, score) tuples sorted by descending score.
    """
    tokens = set(user_input.lower().split())
    input_lower = user_input.lower()

    results = []
    for domain in presets.get("domains", []):
        score = 0.0
        domain_keywords = [k.lower() for k in domain.get("keywords", [])]
        total_keywords = len(domain_keywords) or 1

        for kw in domain_keywords:
            if _matches_input_term(kw, tokens, input_lower):
                score += 1.0

        for source in domain.get("sources", []):
            for tag in source.get("tags", []):
                if _matches_input_term(tag, tokens, input_lower):
                    score += 0.3

        normalized = min(score / total_keywords, 1.0)
        if normalized >= threshold:
            results.append((domain, normalized))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def collect_sources_from_domains(
    matched_domains: List[Tuple[Dict, float]],
) -> List[Dict]:
    """Flatten matched domains into a deduplicated list of source configs.

    Args:
        matched_domains: Output from match_domains().

    Returns:
        List of source dicts (each with type, description, config, origin="preset").
    """
    seen = set()
    sources = []

    for domain, _score in matched_domains:
        for src in domain.get("sources", []):
            key = _source_unique_key(src)
            if key not in seen:
                seen.add(key)
                sources.append({**src, "origin": "preset"})

    return sources


def _tag_matches_input(tag: str, tokens: set, input_lower: str) -> bool:
    """Check if a tag (or any of its aliases) matches the user input."""
    if _matches_input_term(tag, tokens, input_lower):
        return True
    for alias in get_tag_aliases(tag):
        if _matches_input_term(alias, tokens, input_lower):
            return True
    return False


def match_sources(
    user_input: str,
    presets: Dict,
    threshold: float = 0.1,
) -> List[Tuple[Dict, float]]:
    """Match user interest description against individual sources.

    Scores each source based on:
    - Category keyword matches (+1.0 per keyword)
    - Source tag matches (+0.5 per tag)
    - Description word matches (+0.3 per word, min length 3)

    Args:
        user_input: Free-form user interest description (supports mixed languages).
        presets: Loaded presets dictionary.
        threshold: Minimum normalized score to include a source.

    Returns:
        List of (source_dict, score) tuples sorted by descending score.
        Each source_dict has origin="preset" added.
    """
    tokens = set(user_input.lower().split())
    input_lower = user_input.lower()
    total_tokens = len(tokens) or 1

    seen = set()
    results = []

    for domain in presets.get("domains", []):
        domain_keywords = [k.lower() for k in domain.get("keywords", [])]

        category_score = sum(
            1.0 for kw in domain_keywords
            if _matches_input_term(kw, tokens, input_lower)
        )

        for src in domain.get("sources", []):
            key = _source_unique_key(src)
            if key in seen:
                continue
            seen.add(key)

            tag_score = sum(
                0.5 for tag in src.get("tags", [])
                if _tag_matches_input(tag, tokens, input_lower)
            )

            description = src.get("description", "").lower()
            desc_tokens = set(description.split())
            desc_score = sum(
                0.3 for token in tokens
                if len(token) >= 3 and token in desc_tokens
            )

            raw_score = category_score + tag_score + desc_score
            normalized = min(raw_score / total_tokens, 1.0)

            if normalized >= threshold:
                results.append(({**src, "origin": "preset"}, normalized))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def _source_unique_key(source: Dict) -> str:
    """Generate a unique key for a source to enable deduplication."""
    src_type = source.get("type", "")
    cfg = source.get("config", {})

    if src_type == "rss":
        return f"rss:{cfg.get('url', '')}"
    elif src_type == "reddit_subreddit":
        return f"reddit:{cfg.get('subreddit', '')}"
    elif src_type == "reddit_user":
        return f"reddit_user:{cfg.get('username', '')}"
    elif src_type == "github_user":
        return f"github_user:{cfg.get('username', '')}"
    elif src_type == "github_repo":
        return f"github_repo:{cfg.get('owner', '')}/{cfg.get('repo', '')}"
    elif src_type == "telegram":
        return f"telegram:{cfg.get('channel', '')}"
    else:
        return f"{src_type}:{json.dumps(cfg, sort_keys=True)}"
