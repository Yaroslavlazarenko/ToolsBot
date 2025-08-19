from aiogram.fsm.state import State, StatesGroup

class ProcessingState(StatesGroup):
    # Единственное состояние, которое нам нужно.
    # Оно будет как флаг: "пользователь занят".
    is_processing = State()
