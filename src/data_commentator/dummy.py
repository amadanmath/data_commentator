from pandas import DataFrame

from .types import (
    Predictor, PayloadEnhancer, PriorityPredictor,
    Window, History, Payload, Context
)


class DummyPayloadEnhancer(PayloadEnhancer):
    def __call__(self, payload: Payload, _window: Window | None, _meta: str | None = None) -> Payload:
        return payload

class DummyPriorityPredictor(PriorityPredictor):
    def process(self, data: DataFrame, history: History) -> tuple[int, Context]:
        return 1, None

class DummyPredictor(Predictor):
    def __init__(self, text: str = "Hello, world") -> None:
        self.text = text
        super().__init__()

    def __call__(self, window: Window, history: History, context: Context) -> str:
        _ = window
        _ = context
        return self.text
