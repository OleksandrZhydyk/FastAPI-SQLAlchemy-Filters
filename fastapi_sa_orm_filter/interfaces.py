from abc import ABC, abstractmethod

from fastapi_sa_orm_filter.dto import ParsedFilter
from fastapi_sa_orm_filter.operators import Operators as ops


class QueryParser(ABC):

    @abstractmethod
    def __init__(self, custom_filter: str, allowed_filters: dict[str, list[ops]]) -> None:
        self.custom_filter = custom_filter
        self.allowed_filters = allowed_filters

    @abstractmethod
    def get_parsed_filter(self) -> tuple[list[list[ParsedFilter]], list[str]] | tuple[list, list]:
        pass
