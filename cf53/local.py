from collections.abc import Iterable
from pathlib import Path
import tomllib

from .record import Record, RecordType


def load_zones_dir(
    *,
    zones_dir: Path,
    default_comment: str = "",
    only_domains: Iterable[str] | None = None,
) -> dict[str, set[Record]]:
    """Map of domains to records in <zones_dir>/<domain>.toml"""
    zones: dict[str, set[Record]] = {}
    only_domains = set(only_domains or set())

    for toml_file in zones_dir.glob("*.toml"):
        domain = toml_file.stem

        if only_domains and domain not in only_domains:
            continue

        with open(toml_file, "rb") as f:
            toml = tomllib.load(f)

        zones[toml_file.stem] = {
            Record(
                type=record_type,
                name=_normalize_name(record["name"], domain),
                content=f'"{record["content"]}"'
                if record_type == "txt"
                else record["content"],
                ttl=record.get("ttl", 1),  # 1=auto
                proxied=record.get("proxied", False),
                comment=record.get("comment", default_comment),
                priority=record.get("priority") if record_type == "mx" else None,
            )
            for record_type in RecordType
            for record in toml.get(record_type.value, [])
        }

    return zones


def _normalize_name(toml_name: str, domain: str) -> str:
    if toml_name == "@":
        return domain
    if not toml_name.endswith(domain):
        return f"{toml_name}.{domain}"
    return toml_name
