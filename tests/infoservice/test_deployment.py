from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_container_image_has_runtime_and_full_runtime_targets():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "AS runtime" in dockerfile
    assert "AS runtime-full" in dockerfile
    assert "--extra twitter" in dockerfile
    assert "--extra openbb" in dockerfile


def test_production_compose_has_all_infoservice_processes_and_safe_dependencies():
    compose = (ROOT / "docker-compose.yml").read_text()

    for service in ("postgres:", "migrate:", "bot:", "scheduler:", "worker:"):
        assert service in compose
    assert "${APP_IMAGE_TARGET:-runtime}" in compose
    assert "${ENV_FILE:-.env}" in compose
    assert '"uv", "run", "--no-sync", "python", "scripts/healthcheck.py"' in compose
    assert "service_healthy" in compose
    assert "service_completed_successfully" in compose
    assert "./data:/app/data" not in compose


def test_operator_environment_template_contains_only_safe_placeholders():
    template = (ROOT / ".env.example").read_text()

    for name in (
        "DATABASE_URL=",
        "TELEGRAM_BOT_TOKEN=",
        "APP_ENCRYPTION_KEY=",
        "ENABLE_TWITTER=",
        "ENABLE_OPENBB=",
        "MAX_REPORTS_PER_USER=",
        "MAX_SOURCES_PER_REPORT=",
        "APIFY_TOKEN=",
    ):
        assert name in template
    assert "sk-" not in template
