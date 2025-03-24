from typing import Any

import trio
from pydub.audio_segment import AudioSegment
import httpx
import sys

from .types import Window, History, Context
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
            history: History,
    ) -> None:
        self.predictor = predictor
        self.synthesizer = synthesizer
        self.speaker = speaker
        self.priority = priority
        self.history = history

        self.nursery = None
        self.cancel_scope = None
        self.task_id = 0
        super().__init__()

    async def __call__(self, window: Window, history: History, priority: int, context: Context, long_context: Context) -> None:
        task_id = self.task_id
        self.priority.set(priority, task_id, context, long_context)
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
            text = await self.predictor(window, self.history, self.priority.context, self.priority.long_context)
            if text:
                self.history.append(text)
                seg: AudioSegment | None = None
                if self.synthesizer:
                    try:
                        seg = await self.synthesizer(text)
                    except httpx.ConnectError as x:
                        print(f"Cannot connect to the synthesizer: {x}", file=sys.stderr)
                        self.synthesizer = None

                # timestamp = window[-1]["timestamp"]; ic(timestamp, text)
                try:
                    await self.speaker(seg, text)
                finally:
                    self.priority.reset(task_id)
            else:
                self.priority.reset(task_id)
