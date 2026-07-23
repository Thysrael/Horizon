from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    timezone = State()


class Credentials(StatesGroup):
    replace_confirmation = State()
    deepseek_key = State()


class CreateReport(StatesGroup):
    name = State()
    confirmation = State()


class EditRules(StatesGroup):
    threshold = State()
    categories = State()
    exclusions = State()
    max_items = State()
    language = State()
    lookback = State()
    custom_instruction = State()


class EditSchedule(StatesGroup):
    kind = State()
    value = State()


class SourceForm(StatesGroup):
    primary_input = State()
    value_review = State()
    options = State()
    field_input = State()
    summary = State()
    delete_confirmation = State()
