"""Local, webhook-driven Notion to Codex automation for Horizon."""

from .config import AgentConfig
from .webhook import create_app

__all__ = ["AgentConfig", "create_app"]
