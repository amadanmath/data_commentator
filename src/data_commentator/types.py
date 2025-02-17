from abc import abstractmethod
from typing import Any, Callable
from collections import deque
from collections.abc import Awaitable

from pydub.audio_segment import AudioSegment
from pandas import DataFrame


Payload = dict[str, Any]
Window = deque[Payload]
History = deque[Any]

Context = Any
Synthesizer = Callable[[str], Awaitable[AudioSegment | None]]
Speaker = Callable[[AudioSegment | None, str], Awaitable[None]]


class PayloadEnhancer:
    def start(self, payload: Payload) -> None:
        pass

    def __call__(self, payload: Payload, window: Window | None, meta: str | None = None) -> Payload | None:
        pass


class PriorityPredictor:
    @abstractmethod
    def process(self, data: DataFrame, history: History) -> tuple[int, Context]:
        pass

    def __call__(self, window: Window, history: History) -> tuple[int, Context]:
        data: DataFrame = DataFrame(window).to_dict(orient='list')
        return self.process(data, history)


class Predictor:
    @abstractmethod
    def __call__(self, window: Window, history: History, context: Context) -> str:
        pass
