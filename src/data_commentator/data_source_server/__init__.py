from abc import ABC, abstractmethod


class DataSourceServer(ABC):
    @abstractmethod
    async def serve(self) -> None:
        pass
