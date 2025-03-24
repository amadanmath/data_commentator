from dataclasses import dataclass

from .types import Context


@dataclass
class Priority:
    value: int
    task_id: int
    context: Context
    long_context: Context

    def __init__(self) -> None:
        self.value = 0
        self.task_id = 0
        self.context = None
        super().__init__()

    def set(self, value: int, task_id: int, context: Context, long_context: Context) -> None:
        self.value = value
        self.task_id = task_id
        self.context = context
        self.long_context = long_context

    def reset(self, task_id: int) -> None:
        if self.task_id == task_id:
            self.value = 0
            self.context = None
            self.long_context = None
