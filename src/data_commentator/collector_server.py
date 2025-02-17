from collections import deque
from pathlib import Path
import gzip

import trio
import orjson

from .types import Payload, Window, History, Context
from .priority import Priority
from .utterance_server import UtteranceServer
from .async_server import AsyncServer
from .webserver import webserver


class CollectorServer:
    def __init__(self,
        receive_channel: trio.MemoryReceiveChannel[Payload],
        utterance_server: UtteranceServer,
        window_size: int,
        ts_field: str,
        priority: Priority,
        history: History,
        priority_predictor: AsyncServer | None = None,
        payload_enhancer: AsyncServer | None = None,
        output_file: Path | None = None,
        interval: float | None = None,
        start: Payload | None = None,
    ) -> None:
        self.receive_channel = receive_channel
        self.utterance_server = utterance_server
        self.priority_predictor = priority_predictor
        self.payload_enhancer = payload_enhancer
        self.window_size = window_size
        self.current_priority = priority
        self.ts_field = ts_field
        self.output_file = output_file
        self.interval = interval
        self.history: History = history,
        self.start = start

        self.window: Window = deque(maxlen=self.window_size)
        super().__init__()

    async def serve(self):
        start_ts = None
        sample_count = 0
        if self.output_file:
            if self.output_file.name.endswith(".gz"):
                w = gzip.open(self.output_file, "wb")
            else:
                w = self.output_file.open("wb")
        else:
            w = None

        start: Payload | None = self.start
        payload: Payload
        try:
            while True:
                if start:
                    payload = start
                    start = None
                else:
                    payload = await self.receive_channel.receive()

                if w:
                    line: bytes = orjson.dumps(payload)
                    _ = w.write(line + b"\n")
                meta = payload.get("meta")
                if meta:
                    initial_data: Payload = payload
                    if self.payload_enhancer:
                        meta_data = await self.payload_enhancer(initial_data, meta=meta)
                    if meta == "start":
                        webserver.set_initial_data(meta_data)
                        self.window.clear()
                    elif meta == "end":
                        webserver.set_initial_data({})
                        pass
                    await webserver.broadcast(payload)
                else:
                    now = payload[self.ts_field]
                    if start_ts is None:
                        start_ts = now

                    if self.interval is None or now >= start_ts + self.interval * sample_count:
                        sample_count += 1
                    else:
                        continue

                    if self.payload_enhancer:
                        payload = await self.payload_enhancer(payload, self.window)
                        if not payload:
                            continue
                    self.window.append(payload)

                    await webserver.broadcast(payload)

                    predicted_priority: int
                    context: Context
                    if self.priority_predictor:
                        predicted_priority, context = await self.priority_predictor(self.window, self.history) # XXX: Investigate intermittent error
                    else:
                        predicted_priority = 1
                        context = None
                    if predicted_priority > self.current_priority.value:
                        await self.utterance_server(self.window, self.history, predicted_priority, context)
        finally:
            if w:
                w.close()
