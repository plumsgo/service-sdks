from typing import Iterable


def parse_issuers(value: str | Iterable[str] | None) -> frozenset[str]:
    """Turn a comma-separated env value or an iterable into an allow-list.

    Empty input is an empty set: no service caller is accepted. This is not
    the same as ``allowed_issuers=None`` on ``GateAuth``, which means unrestricted.
    """
    if value is None:
        return frozenset()
    if isinstance(value, str):
        parts = value.split(",")
    else:
        parts = [str(item) for item in value]
    return frozenset(item.strip() for item in parts if item.strip())
