from pandas import DataFrame

from .types import (
    Predictor, PayloadEnhancer, PriorityPredictor,
    Window, History, Payload, Context
)


class DummyPayloadEnhancer(PayloadEnhancer):
    def __call__(self, payload: Payload, long_context: Payload, window: Window | None, meta: str | None) -> Payload | None:
        _ = meta
        _ = long_context
        return payload

class DummyPriorityPredictor(PriorityPredictor):
    def process(self, data: DataFrame, history: History, long_context: Context) -> tuple[int, Context]:
        return 1, {}

class DummyPredictor(Predictor):
    def __init__(self, text: str = "Hello, world") -> None:
        self.text = text
        super().__init__()

    def __call__(self, window: Window, history: History, context: Context, long_context: Context) -> str:
        _ = window
        _ = context
        _ = long_context
        return self.text
