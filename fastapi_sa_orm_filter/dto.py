from dataclasses import dataclass


@dataclass
class ParsedFilter:
    field_name: str
    operator: str
    value: str
    relation: str | None

    @property
    def has_relation(self) -> bool:
        return bool(self.relation)
