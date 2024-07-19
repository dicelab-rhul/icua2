from typing import List, Dict, Any, Callable
from abc import ABC, abstractmethod


class EyetrackerBase(ABC):

    def __init__(
        self,
        *args,
        filters: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._filters = filters if filters else []

    def get_filters(self):
        return self._filters

    def apply_filters(self, data: Dict[str, Any]):
        for _filter in self._filters:
            data = _filter(data)
        return data

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    async def get(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_nowait(self) -> List[Dict[str, Any]]:
        pass
