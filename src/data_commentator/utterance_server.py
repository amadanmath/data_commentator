from typing import Any

import trio
from pydub.audio_segment import AudioSegment

from .types import Window, Context
from .async_server import AsyncServer
from .synthesizer import Synthesizer
from .speaker import Speaker
from .priority import Priority


class UtteranceServer:
    def __init__(
            self,
            predictor: AsyncServer,
            synthesizer: Synthesizer,
            speaker: Speaker,
            priority: Priority,
    ) -> None:
        self.predictor = predictor
        self.synthesizer = synthesizer
        self.speaker = speaker
        self.priority = priority

        self.nursery = None
        self.cancel_scope = None
        self.task_id = 0
        super().__init__()

    async def __call__(self, window: Window, priority: int, context: Context) -> None:
        task_id = self.task_id
        self.priority.set(priority, task_id, context)
        self.task_id += 1
        if self.nursery:
            if self.cancel_scope:
                _ = self.cancel_scope.cancel()
                self.cancel_scope = None
            try:
                self.cancel_scope = await self.nursery.start(self.predict_text, window, task_id)
            except RuntimeError:
                pass # If we can't start the task, it is not worth starting (program ending)

    async def serve(self) -> None:
        async with trio.open_nursery() as nursery:
            self.nursery = nursery
            await trio.sleep_forever()

    async def predict_text(self, window: Window, task_id: int, *, task_status: trio.TaskStatus[Any]=trio.TASK_STATUS_IGNORED):
        with trio.CancelScope() as scope:
            task_status.started(scope)
            text = await self.predictor(window, self.priority.context)
            if text:
                seg: AudioSegment | None = None
                if self.synthesizer:
                    seg = await self.synthesizer(text)

                # timestamp = window[-1]["timestamp"]; ic(timestamp, text)
                try:
                    await self.speaker(seg, text)
                finally:
                    self.priority.reset(task_id)
            else:
                self.priority.reset(task_id)
