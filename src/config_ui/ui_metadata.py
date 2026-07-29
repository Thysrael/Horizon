"""Stable, hand-maintained hints layered on top of the Pydantic schema."""


SECTIONS = [
    "overview",
    "quick_setup",
    "ai",
    "sources",
    "extractors",
    "filtering",
    "delivery",
    "advanced_json",
    "backups",
]

UI_METADATA = {
    "sections": SECTIONS,
    "field_order": [
        "version",
        "ai",
        "sources",
        "extractors",
        "filtering",
        "domains",
        "domain_concurrency",
        "github_pages",
        "email",
        "webhook",
    ],
    "controls": {
        "/ai/temperature": "number",
        "/webhook/headers": "textarea",
        "/webhook/request_body": "json",
    },
    "conditions": [
        {
            "path": "/ai/azure_endpoint_env",
            "when": {"path": "/ai/provider", "equals": "azure"},
            "preserve_when_hidden": True,
        }
    ],
}
