from src.infoservice.bot.keyboards import (
    accepted_value_menu,
    field_menu,
    primary_input_menu,
    source_catalog_menu,
    source_menu,
    source_options_menu,
    summary_menu,
)
from src.infoservice.bot.states import SourceForm


def labels(markup):
    return [button.text for row in markup.inline_keyboard for button in row]


def test_source_wizard_has_explicit_states():
    assert SourceForm.primary_input.state.endswith(":primary_input")
    assert SourceForm.value_review.state.endswith(":value_review")
    assert SourceForm.options.state.endswith(":options")
    assert SourceForm.field_input.state.endswith(":field_input")
    assert SourceForm.summary.state.endswith(":summary")


def test_catalog_contains_only_four_stable_sources():
    assert labels(source_catalog_menu("report-id")) == [
        "🟠 RSS / Atom",
        "🔵 Telegram-канал",
        "⚫ GitHub",
        "🟠 Hacker News",
        "‹ Назад",
        "Отмена",
    ]


def test_first_two_steps_have_explicit_next_action():
    assert "Далее →" in labels(accepted_value_menu())
    assert "Далее →" in labels(source_options_menu())
    assert labels(primary_input_menu()) == ["‹ Назад", "Отмена"]


def test_summary_and_edit_keyboards_are_human_readable():
    assert labels(summary_menu()) == [
        "✅ Сохранить источник", "✏️ Изменить", "‹ Назад", "Отмена",
    ]
    assert labels(field_menu("telegram")) == [
        "Категория", "Количество сообщений", "Готово", "‹ Назад", "Отмена",
    ]


def test_beta_source_has_no_edit_button():
    assert "Изменить" not in labels(source_menu("source-id", True, editable=False))
