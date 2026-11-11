"""Host-model exchange configuration; no hidden account or canned response."""
from dataclasses import asdict, dataclass
import re

from ..errors import ContractError


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    reasoning_level: str = "provider_default"
    timeout_seconds: int = 300
    max_request_bytes: int = 524288
    max_output_bytes: int = 131072
    max_attempts_per_chapter: int = 2
    max_requests: int = 24

    def to_dict(self):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}", self.model_id):
            raise ContractError("MODEL_ID_REQUIRED")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", self.reasoning_level):
            raise ContractError("MODEL_REASONING_CONFIG")
        for value, upper in ((self.timeout_seconds, 3600), (self.max_request_bytes, 2097152),
                             (self.max_output_bytes, 1048576), (self.max_attempts_per_chapter, 3),
                             (self.max_requests, 64)):
            if type(value) is not int or not 1 <= value <= upper:
                raise ContractError("MODEL_BUDGET_CONFIG")
        return asdict(self)


def integration_status():
    return {"status": "MODEL_INTEGRATION_BLOCKED", "transport": "HOST_FILE_EXCHANGE",
            "reason": "No authorized host execution receipt or installed model adapter has been verified.",
            "automatic_calls": False, "credentials_read": False}
