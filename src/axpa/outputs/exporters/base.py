from abc import ABC, abstractmethod

class BaseExporter(ABC):
    @abstractmethod
    async def export(self, results: dict, destination: str):
        pass