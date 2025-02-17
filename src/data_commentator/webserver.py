import logging
from pathlib import Path

import trio
import orjson
from quart_trio import QuartTrio
from quart.json.provider import DefaultJSONProvider
from quart_trio.wrappers.websocket import TrioWebsocket
from quart import request, websocket, redirect
from typing import Any
import numpy as np

from .types import Payload



def json_default(obj: Any):
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_)):
        return float(obj)
    elif isinstance(obj, np.ndarray):  
        return obj.tolist()  # Convert numpy arrays to lists
    raise TypeError(f"Type {type(obj)} not serializable")

class ORJSONProvider(DefaultJSONProvider):
    def dumps(self, obj: Any, **kwargs: dict[str, Any]):
        return orjson.dumps(obj, default=json_default).decode()

    def loads(self, s: str | bytes, **kwargs: dict[str, Any]):
        return orjson.loads(s)


class Webserver:
    def __init__(self, app: QuartTrio) -> None:
        self.app = app
        self.data_send_channel: trio.MemorySendChannel[Payload] | None = None
        self.initial_data: Payload | None = None
        self.bind = "0.0.0.0"
        self.port = 5007
        self.connections: set[TrioWebsocket] = set()
        super().__init__()

    def set_initial_data(self, initial_data: Payload):
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
app.json = ORJSONProvider(app)


@app.route('/', methods=['GET'])
async def index() -> tuple[bytes, Any]:
    return redirect("/index.html")

@app.route('/data', methods=['POST'])
async def data() -> tuple[bytes, Any]:
    body: bytes = await request.get_data()
    payloads: list[Payload] = [orjson.loads(line) for line in body.strip().split(b'\n')]
    ignored_payloads = 0
    if webserver.data_send_channel:
        for payload in payloads:
            try:
                webserver.data_send_channel.send_nowait(payload)
            except trio.WouldBlock:
                ignored_payloads += 1
    if ignored_payloads:
        app.logger.warning(f'Ignored {ignored_payloads}/{len(payloads)} ({100 * ignored_payloads / len(payloads)}%)')
    return b'', 204 # No Response

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
