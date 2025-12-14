from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any


class RecordType(StrEnum):
    a = auto()
    aaaa = auto()
    mx = auto()
    txt = auto()
    cname = auto()


@dataclass(frozen=True, slots=True)
class Record:
    type: RecordType
    name: str
    content: str
    ttl: int
    proxied: bool
    comment: str
    priority: int | None = None
    cloudflare_id: str | None = None

    def __post_init__(self) -> None:
        if self.priority and not self.type == "mx":
            raise ValueError("priority can only be set for mx records")

    def __eq__(self, other: Any) -> bool:
        """Equality should ignore a `None` cloudflare_id."""
        if not isinstance(other, Record):
            return False
        return (
            self.type == other.type
            and self.name == other.name
            and self.content == other.content
            and self.ttl == other.ttl
            and self.proxied == other.proxied
            and self.comment == other.comment
            and self.priority == other.priority
            and (
                self.cloudflare_id == other.cloudflare_id
                or self.cloudflare_id is None
                or other.cloudflare_id is None
            )
        )
