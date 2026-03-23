from typing import List

from src.core.performops.model import UserAction


class UserActionStore:
    _actions: List[UserAction] = []

    @classmethod
    def set(cls, actions: List[UserAction]) -> None:
        cls._actions = actions

    @classmethod
    def get(cls) -> List[UserAction]:
        return cls._actions
