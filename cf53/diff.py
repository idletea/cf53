from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .console import console
from .record import Record, RecordType


@dataclass(frozen=True, slots=True)
class Update:
    initial: Record
    desired: Record


@dataclass(frozen=True, slots=True)
class Diff:
    domain: str
    zone_id: str
    to_create: set[Record]
    to_update: set[Update]
    to_delete: set[Record]
    in_sync: set[Record]

    @classmethod
    def from_zones(
        cls,
        *,
        domain: str,
        zone_id: str,
        local_zone: set[Record],
        remote_zone: set[Record],
    ) -> Self:
        to_create = set()
        to_update = set()
        to_delete = set()
        in_sync = set()

        # lookup to match remote records semantically identical to local records, where
        # records match in this way we can do an update rather than create/delete
        unmatched_remote_records: dict[
            tuple[RecordType, str, str, int | None], Record
        ] = {_semantic_key(r): r for r in remote_zone}

        # local records must be created or matched to a remote record to update in-place
        for local_record in local_zone:
            key = _semantic_key(local_record)

            if matching_remote_record := unmatched_remote_records.get(key):
                del unmatched_remote_records[key]

                if local_record == matching_remote_record:
                    in_sync.add(matching_remote_record)
                else:
                    to_update.add(
                        Update(
                            initial=matching_remote_record,
                            desired=local_record,
                        )
                    )
            else:
                to_create.add(local_record)

        to_delete = set(unmatched_remote_records.values())

        return cls(
            domain=domain,
            zone_id=zone_id,
            to_create=to_create,
            to_update=to_update,
            to_delete=to_delete,
            in_sync=in_sync,
        )

    def print(self) -> None:
        if not self:
            console.print(f"✓ {self.domain}", style="dim white")
            return

        console.print(f"~ {self.domain}", style="bold blue")
        for r in self.to_create:
            self._print_record(r, icon="+", style="bold green")
        for update in self.to_update:
            r = update.desired
            self._print_record(r, icon="~", style="bold yellow")
        for r in self.to_delete:
            self._print_record(r, icon="-", style="bold red")

    def _print_record(self, r: Record, icon: str, style: str):
        proxied = "    proxied"
        if not r.proxied:
            proxied = "not proxied"
        priority = ""
        if r.type == "mx":
            priority = f"{r.priority:4} "
        ttl = int(r.ttl)
        if ttl == 1:
            ttl = "auto"
        console.print(f"  {icon} {r.type.upper():5} {r.name}", style=style)
        console.print(f'    {proxied}  | {ttl:4} |  "{r.comment}"')
        console.print(f"      {priority}{r.content}", style="italic")

    def __bool__(self) -> bool:
        return any((self.to_create, self.to_delete, self.to_update))


def _semantic_key(record: Record) -> tuple[RecordType, str, str, int | None]:
    return (record.type, record.name, record.content, record.priority)
