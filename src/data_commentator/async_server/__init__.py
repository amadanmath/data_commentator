from abc import abstractmethod
from typing import Any


class AsyncServer:
    @abstractmethod
    async def serve(self):
        pass

    @abstractmethod
    async def __call__(self, *args: Any, **kwargs: Any):
        pass
