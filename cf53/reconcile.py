import asyncio
from collections.abc import Iterable

from cloudflare import AsyncCloudflare

from .diff import Diff


async def _reconcile_diff(diff: Diff, client: AsyncCloudflare) -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(_apply_creates_async(diff, client))
        tg.create_task(_apply_updates_async(diff, client))
        tg.create_task(_apply_deletes_async(diff, client))


def reconcile_diffs(diffs: Iterable[Diff], client: AsyncCloudflare) -> None:
    async def main():
        async with asyncio.TaskGroup() as tg:
            for diff in diffs:
                tg.create_task(_reconcile_diff(diff, client))

    asyncio.run(main())


async def _apply_creates_async(diff: Diff, client: AsyncCloudflare) -> None:
    for record in diff.to_create:
        record_data = {
            "type": record.type.value,
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl,
            "proxied": record.proxied,
            "comment": record.comment,
        }
        if record.priority is not None:
            record_data["priority"] = record.priority

        await client.dns.records.create(zone_id=diff.zone_id, **record_data)  # type: ignore[no-matching-overload]


async def _apply_updates_async(diff: Diff, client: AsyncCloudflare) -> None:
    for update in diff.to_update:
        record_data = {
            "type": update.desired.type.value,
            "name": update.desired.name,
            "content": update.desired.content,
            "ttl": update.desired.ttl,
            "proxied": update.desired.proxied,
            "comment": update.desired.comment,
        }

        if update.desired.priority is not None:
            record_data["priority"] = update.desired.priority

        await client.dns.records.update(  # type: ignore[no-matching-overload]
            update.initial.cloudflare_id,
            zone_id=diff.zone_id,
            **record_data,
        )


async def _apply_deletes_async(diff: Diff, client: AsyncCloudflare) -> None:
    for record in diff.to_delete:
        assert record.cloudflare_id
        await client.dns.records.delete(
            record.cloudflare_id,
            zone_id=diff.zone_id,
        )
