from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    timezone = State()


class Credentials(StatesGroup):
    replace_confirmation = State()
    deepseek_key = State()
