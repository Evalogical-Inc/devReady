from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"  # something worth fixing, not blocking
    FAIL = "fail"  # blocking: a requirement is not met
    SKIP = "skip"  # check not enabled / not applicable
    ERROR = "error"  # DevReady could not perform the check


@dataclass(frozen=True)
class Result:
    check_id: str
    title: str
    status: Status
    summary: str
    suggestion: str = ""
    docs_url: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d
