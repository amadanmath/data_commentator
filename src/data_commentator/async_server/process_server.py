from typing import Any
from multiprocessing import Process, Pipe
from threading import Thread
try:
    from multiprocessing.connection import PipeConnection as Connection
except ImportError:
    from multiprocessing.connection import Connection

import trio

from . import AsyncServer


def serve_process(pipe: Connection, constructor: Any, *args: Any, **kwargs: Any) -> None:
    try:
        processor = constructor(*args, **kwargs)
        while True:
            [args, kwargs] = pipe.recv()
            output: Any = processor(*args, **kwargs)
            pipe.send(output)
    except KeyboardInterrupt:
        pass


# With help from https://stackoverflow.com/a/78140032/240443
class ProcessServer(AsyncServer):
    def __init__(self, constructor: Any, *args: Any, **kwargs: Any) -> None:
        pipe: tuple[Connection, Connection] = Pipe()
        self._pipe, child_pipe = pipe

        data_channel: tuple[trio.MemorySendChannel[Any], trio.MemoryReceiveChannel[Any]] = trio.open_memory_channel(1)
        self._send_channel, self._recv_channel = data_channel

        self._trio_token = trio.lowlevel.current_trio_token()
        self._recv_thread_running = False
        self._recv_thread = Thread(target=self._serve_recv_thread)
        self._stopped_event = trio.Event()
        self._cancel_scope = None

        self._process = Process(target=serve_process, args=[child_pipe, constructor, *args], kwargs=kwargs)
        super().__init__()

    async def serve(self) -> None:
        try:
            self._recv_thread.start()
            self._process.start()
            with trio.CancelScope() as cancel_scope:
                self._cancel_scope = cancel_scope
                await trio.sleep_forever()
        finally:
            self._recv_thread_running = False
            self._process.terminate()
            with trio.CancelScope(shield=True):
                await self._stopped_event.wait()
                self._recv_thread.join()

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        try:
            self._pipe.send([args, kwargs])
            output = await self._recv_channel.receive()
            return output
        except BrokenPipeError:
            if self._cancel_scope:
                self._cancel_scope.cancel()
            trio.lowlevel.current_task().parent_nursery.cancel_scope.cancel()

    def _serve_recv_thread(self) -> None:
        self._recv_thread_running = True
        try:
            while self._recv_thread_running:
                if self._pipe.poll(1):
                    data = self._pipe.recv()
                    self._trio_token.run_sync_soon(self._send_channel.send_nowait, data)
        except EOFError:
            pass # Done
        self._trio_token.run_sync_soon(self._stopped_event.set)


import time
class ServedProcess:
    def __init__(self, x: int):
        print(f"SP:INIT: {x}")
        super().__init__()

    def __call__(self, n: int, foo: int):
        print(f"SP:CALL {n} {foo}")
        time.sleep(1)
        return True

if __name__ == "__main__":
    async def main():
        process_server = ProcessServer(ServedProcess, 6)
        with trio.move_on_after(4):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(process_server.serve)
                res = await process_server(3, foo=4)
                print(f"DONE: {res}")
                res = await process_server(1, foo=2)
                print(f"DONE: {res}")

    trio.run(main)
