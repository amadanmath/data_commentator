from typing import Any

import trio

from . import AsyncServer


class CallServer(AsyncServer):
    def __init__(self, constructor: Any, *args: Any, **kwargs: Any) -> None:
        self.processor = constructor(*args, **kwargs)
        super().__init__()

    async def serve(self):
        pass

    async def __call__(self, *args: Any, **kwargs: Any):
        output = self.processor(*args, **kwargs)
        return output


import time
class ServedCall:
    def __init__(self, x: int):
        print(f"SP:INIT: {x}")
        super().__init__()

    def __call__(self, n: int, foo: int):
        print(f"SP:CALL {n} {foo}")
        time.sleep(1)
        return True

if __name__ == "__main__":
    async def main():
        call_server = CallServer(ServedCall, 6)
        with trio.move_on_after(4):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(call_server.serve)
                res = await call_server(3, foo=4)
                print(f"DONE: {res}")
                res = await call_server(1, foo=2)
                print(f"DONE: {res}")

    trio.run(main)

