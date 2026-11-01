"""Extractor registry."""

from typing import Dict, Optional

from .base import BaseExtractor
from .firecrawl import FirecrawlExtractor
from .trafilatura import TrafilaturaExtractor
from ..models import (
    ExtractorConfig,
    ExtractorType,
    FirecrawlExtractorConfig,
    TrafilaturaExtractorConfig,
)

_DEFAULTS: Dict[str, ExtractorConfig] = {
    ExtractorType.TRAFILATURA: TrafilaturaExtractorConfig(),
    ExtractorType.FIRECRAWL: FirecrawlExtractorConfig(),
}


def _build(cfg: ExtractorConfig) -> BaseExtractor:
    match cfg:
        case TrafilaturaExtractorConfig():
            return TrafilaturaExtractor(cfg)
        case FirecrawlExtractorConfig():
            return FirecrawlExtractor(cfg)
        case _:
            raise NotImplementedError(f"Extractor type '{cfg.type}' is not yet implemented")


class ExtractorRegistry:
    def __init__(self, config: Dict[str, ExtractorConfig]):
        self._extractors: Dict[str, BaseExtractor] = {
            name: _build(cfg) for name, cfg in _DEFAULTS.items()
        }
        self._extractors.update({
            name: _build(cfg) for name, cfg in config.items()
        })

    def get(self, name: str) -> Optional[BaseExtractor]:
        return self._extractors.get(name)
