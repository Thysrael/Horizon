"""Terminal icon sets used by Horizon's console output."""

from typing import Literal


IconStyle = Literal["emoji", "nerd", "ascii"]


ICON_SETS: dict[IconStyle, dict[str, str]] = {
    "emoji": {
        "start": "🌅",
        "email": "📧",
        "date": "📅",
        "fetch": "🔍",
        "fetched": "📥",
        "merge": "🔗",
        "ai": "🤖",
        "filter": "⭐️",
        "cleanup": "🧹",
        "balance": "⚖️",
        "discussion": "💬",
        "enrich": "📚",
        "summary": "📝",
        "save": "💾",
        "document": "📄",
        "webhook": "🔔",
        "webhook_skip": "🔕",
        "wechat": "💚",
        "tokens": "🧮",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "detail": "•",
    },
    "nerd": {
        "start": "\uf04b",
        "email": "\uf0e0",
        "date": "\uf073",
        "fetch": "\uf002",
        "fetched": "\uf019",
        "merge": "\uf0c1",
        "ai": "\uf544",
        "filter": "\uf005",
        "cleanup": "\uf51a",
        "balance": "\uf24e",
        "discussion": "\uf086",
        "enrich": "\uf518",
        "summary": "\uf044",
        "save": "\uf0c7",
        "document": "\uf15c",
        "webhook": "\uf0f3",
        "webhook_skip": "\uf1f6",
        "wechat": "\uf1d7",
        "tokens": "\uf1ec",
        "success": "\uf058",
        "warning": "\uf071",
        "error": "\uf057",
        "detail": "\uf444",
    },
    "ascii": {
        "start": ">",
        "email": "@",
        "date": "#",
        "fetch": ">",
        "fetched": "v",
        "merge": ">",
        "ai": "*",
        "filter": "*",
        "cleanup": "-",
        "balance": "=",
        "discussion": ":",
        "enrich": "+",
        "summary": "=",
        "save": ">",
        "document": "#",
        "webhook": "@",
        "webhook_skip": "-",
        "wechat": "W",
        "tokens": "#",
        "success": "+",
        "warning": "!",
        "error": "x",
        "detail": "-",
    },
}


def get_icons(style: IconStyle = "emoji") -> dict[str, str]:
    """Return the icon set for a configured terminal style."""
    return ICON_SETS[style]
