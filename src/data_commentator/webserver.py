import logging
from pathlib import Path

import trio
from quart_trio import QuartTrio
from quart_trio.wrappers.websocket import TrioWebsocket
from quart import request, websocket
from flask_orjson import OrjsonProvider
from typing import Any

from .types import Payload


class Webserver:
    def __init__(self, app: QuartTrio) -> None:
        self.app = app
        self.data_send_channel: trio.MemorySendChannel[Payload] | None = None
        self.initial_data: dict[str, Any] | None = None
        self.bind = "0.0.0.0"
        self.port = 5007
        self.connections: set[TrioWebsocket] = set()
        super().__init__()

    def set_initial_data(self, initial_data: dict[str, Any]):
        self.initial_data = initial_data

    def setup(
        self,
        static_folder: Path,
        data_send_channel: trio.MemorySendChannel[Payload] | None,
        bind: str = "0.0.0.0",
        port: int = 5007,
    ):
        self.data_send_channel = data_send_channel
        self.bind = bind
        self.port = port
        self.app.static_folder = static_folder

    async def broadcast(self, data: dict[str, Any]):
        async with trio.open_nursery() as nursery:
            for connection in self.connections:
                nursery.start_soon(connection.send_json, data)

    async def serve(self):
        async with trio.open_nursery() as nursery:
            # "Warning: The config `debug` has no affect when using serve"
            nursery.start_soon(self.app.run_task, self.bind, self.port, False)


logging.getLogger('hypercorn.access').disabled = True

app = QuartTrio(__name__, static_url_path="")
app.json = OrjsonProvider(app)

@app.route('/data', methods=['POST'])
async def data() -> dict[str, Any]:
    payload: Payload = await request.get_json()
    result: Payload
    try:
        if webserver.data_send_channel:
            webserver.data_send_channel.send_nowait(payload)
            result = {}
        else:
            result = { "warning": "not ready" }
    except trio.WouldBlock:
        result = { "warning": "ignored" }
    return result

@app.websocket('/ws')
async def ws():
    connection: TrioWebsocket = websocket._get_current_object()
    webserver.connections.add(connection)
    try:
        async with trio.open_nursery() as nursery:
            await websocket.send_json({
                "connect": True,
                **(webserver.initial_data or {}),
            })
            nursery.start_soon(trio.sleep_forever)
    finally:
        webserver.connections.remove(connection)


webserver = Webserver(app)


if __name__ == "__main__":
    async def main():
        async with trio.open_nursery() as nursery:
            async def send_stuff_soon():
                _ = await trio.sleep(10)
                await webserver.broadcast({ "payload": "PAAAAAYLOOOAAAAD" })
            nursery.start_soon(send_stuff_soon)
            webserver.setup(
                Path(__file__).parent.parent / 'overlay.html',
                None,
            )
            webserver.set_initial_data({ "greeting": "Hello" })
            await webserver.serve()
    trio.run(main)
