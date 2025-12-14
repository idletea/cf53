from __future__ import annotations

import asyncio

from cloudflare import AsyncCloudflare

from .record import Record, RecordType


async def load_remote_zones(
    client: AsyncCloudflare, domains: set[str]
) -> dict[tuple[str, str], set[Record]]:
    """Map of (domain, zone_id) to records in cloudflare"""
    domain_to_zone_id = {
        zone.name: zone.id
        for zone in _unpage(await client.zones.list())
        if zone.name in domains
    }

    tasks = []
    async with asyncio.TaskGroup() as tg:
        for domain, zone_id in domain_to_zone_id.items():
            task = tg.create_task(_load_remote_zone(client, domain, zone_id))
            tasks.append(task)

    remote_zones: dict[tuple[str, str], set[Record]] = {}
    for task in tasks:
        domain, records = task.result()
        remote_zones[(domain, domain_to_zone_id[domain])] = records

    return remote_zones


async def _load_remote_zone(
    client, domain: str, zone_id: str
) -> tuple[str, set[Record]]:
    records_page = await client.dns.records.list(zone_id=zone_id)
    return (
        domain,
        {
            Record(
                type=RecordType(record.type.lower()),
                name=record.name,
                content=record.content,
                ttl=record.ttl,
                proxied=record.proxied,
                comment=record.comment,
                priority=int(record.priority) if hasattr(record, "priority") else None,
                cloudflare_id=record.id,
            )
            for record in _unpage(records_page)
        },
    )


def _unpage(page):
    for item in page:
        values_type, values = item
        if values_type != "result":
            continue
        yield from values
