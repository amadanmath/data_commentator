from abc import abstractmethod
from typing import Any, Callable
from collections import deque
from collections.abc import Awaitable

from pydub.audio_segment import AudioSegment


Payload = dict[str, Any]
Window = deque[Payload]

Context = Any
Synthesizer = Callable[[str], Awaitable[AudioSegment | None]]
Speaker = Callable[[AudioSegment | None, str], Awaitable[None]]


class PayloadEnhancer:
    def start(self, payload: Payload) -> None:
        pass

    @abstractmethod
    def __call__(self, payload: Payload, window: Window | None, meta: str | None = None) -> Payload:
        pass


class PriorityPredictor:
    @abstractmethod
    def __call__(self, window: Window) -> tuple[int, Context]:
        pass

class Predictor:
    @abstractmethod
    def __call__(self, window: Window, context: Context) -> str:
        pass
