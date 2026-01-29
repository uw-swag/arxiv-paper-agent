from abc import ABC, abstractmethod

class BaseExporter(ABC):

    @abstractmethod
    def export(self, result: dict, destination: str) -> dict:
        pass