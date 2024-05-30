from pathlib import Path
from datetime import datetime
import gzip

import trio
import orjson

from . import DataSourceServer
from ..types import Payload


class JSONLReader(DataSourceServer):
    def __init__(self, send_channel: trio.MemorySendChannel[Payload], jsonl: Path, ts_field: str) -> None:
        super().__init__()
        self.send_channel = send_channel
        self.jsonl = jsonl
        self.ts_field = ts_field

    async def serve(self) -> None:
        dt: datetime
        ts: float
        start_dt: datetime | None = None
        start_ts: float | None = None

        r = gzip.open(self.jsonl, "rb") if self.jsonl.name.endswith(".gz") else self.jsonl.open("rb")
        async with self.send_channel:
            with r:
                for line in r:
                    payload: Payload = orjson.loads(line)
                    ts = payload[self.ts_field]
                    dt = datetime.now()
                    if not (start_ts and start_dt):
                        start_ts = ts
                        start_dt = dt
                    else:
                        wait_time: float = ts - start_ts - (dt - start_dt).total_seconds()
                        if wait_time > 0:
                            await trio.sleep(wait_time)
                    try:
                        self.send_channel.send_nowait(payload)
                    except trio.WouldBlock:
                        pass # ignored
