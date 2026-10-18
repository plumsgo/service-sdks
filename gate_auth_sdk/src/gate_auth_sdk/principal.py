from dataclasses import dataclass, field
from typing import FrozenSet, Literal, Optional


@dataclass(frozen=True)
class Principal:
    """Caller after a gate accepted a user token or an inbound service ticket."""

    sub: Optional[str]
    sid: Optional[str]
    admin: bool
    via: Literal["user", "service"]
    caller: str
    scopes: FrozenSet[str] = field(default_factory=frozenset)

    def is_admin(self) -> bool:
        return self.admin

    def has_scope(self, scope: str) -> bool:
        want = str(scope or "").strip()
        return bool(want) and (self.admin or want in self.scopes)
