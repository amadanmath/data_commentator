import logging
from pathlib import Path

import trio
from quart_trio import QuartTrio
from quart import request, websocket
from flask_orjson import OrjsonProvider
from typing import Any
import orjson

from . import DataSourceServer
from ..types import Payload


logging.getLogger('hypercorn.access').disabled = True

here_dir = Path(__file__).parent

class Webserver(DataSourceServer):
    def __init__(self, send_channel: trio.MemorySendChannel[Payload], bind: str = "127.0.0.1", port: int = 5007) -> None:
        super().__init__()
        self.bind = bind
        self.port = port
        self.initial_data: dict[str, Any] | None = None

        self.app = QuartTrio(__name__)
        self.app.json = OrjsonProvider(self.app)

        @self.app.route('/data', methods=['POST'])
        async def data():
            payload: Payload = await request.get_json()
            result: Payload
            try:
                send_channel.send_nowait(payload)
                result = {}
            except trio.WouldBlock:
                result = { "warning": "ignored" }
            return result

        @self.app.route('/overlay', methods=['GET'])
        async def overlay():
            index_html = (here_dir / 'index.html').read_text(encoding='utf-8')
            return index_html

        # TODO: VERY unfinished!
        @self.app.websocket('/ws')
        async def ws():
            async with trio.open_nursery() as nursery:
                if self.initial_data:
                    await websocket.send(orjson.dumps({ "initial": self.initial_data }))
                nursery.start_soon(self.ws_handler) # TODO: see what arguments are needed

    # TODO: VERY unfinished!
    async def ws_handler(self):
        pass

    async def serve(self) -> None:
        async with trio.open_nursery() as nursery:
            # "Warning: The config `debug` has no affect when using serve"
            nursery.start_soon(self.app.run_task, self.bind, self.port, False)
