from __future__ import annotations

import asyncio
import os
from pathlib import Path

import click
from cloudflare import AsyncCloudflare

from .console import console
from .diff import Diff
from .local import load_zones_dir
from .reconcile import _reconcile_diff
from .remote import load_remote_zones


@click.command()
@click.argument("zones_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--domain",
    "domains",
    multiple=True,
    help="Only process these domains (can be specified multiple times)",
)
@click.option(
    "--default-comment",
    "default_comment",
    help="Comment to append to any record not explicitly commented",
)
@click.option(
    "--ignore-comment",
    "ignore_comment",
    help="Ignore any remote records with this exact comment",
)
def main(
    zones_dir: str,
    domains: tuple[str, ...],
    default_comment: str = "",
    ignore_comment: str = "",
) -> None:
    asyncio.run(
        _async_main(
            zones_dir=Path(zones_dir),
            domains=domains,
            default_comment=default_comment,
            ignore_comment=ignore_comment,
        )
    )


async def _async_main(
    zones_dir: Path,
    domains: tuple[str, ...],
    default_comment: str = "",
    ignore_comment: str = "",
) -> None:
    client = _client()

    with console.status("fetching zones..."):
        local_zones = load_zones_dir(
            zones_dir=zones_dir,
            default_comment=default_comment,
            only_domains=domains,
        )
        remote_zones = await load_remote_zones(
            client=client,
            domains=set(local_zones.keys()),
            ignore_comment=ignore_comment,
        )

    diffs = [
        Diff.from_zones(
            domain=domain,
            zone_id=zone_id,
            local_zone=local_zones[domain],
            remote_zone=remote_zone,
        )
        for (domain, zone_id), remote_zone in remote_zones.items()
    ]

    for diff in diffs:
        diff.print()

    if any(diffs) and await asyncio.to_thread(_user_confirmation):
        await _async_reconcile_diffs(diffs, client)


async def _async_reconcile_diffs(diffs: list[Diff], client: AsyncCloudflare) -> None:
    async with asyncio.TaskGroup() as tg:
        for diff in diffs:
            tg.create_task(_reconcile_diff(diff, client))


def _user_confirmation() -> bool:
    while True:
        response = input("Apply these changes? [y/N] ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no", ""):
            return False


def _client() -> AsyncCloudflare:
    if not (api_token := os.environ.get("CLOUDFLARE_API_TOKEN")):
        raise RuntimeError("CLOUDFLARE_API_TOKEN must be defined")
    return AsyncCloudflare(api_token=api_token)
