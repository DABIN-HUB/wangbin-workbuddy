"""Stable, value-free public errors and validation issues."""
from dataclasses import asdict, dataclass


class ContractError(ValueError):
    def __init__(self, code: str, field_id: str | None = None):
        self.code = code
        self.field_id = field_id
        super().__init__(code + (f": {field_id}" if field_id else ""))


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    field_id: str
    message: str
    severity: str = "ERROR"
    instance_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
