from copy import replace

from cf53.diff import Diff
from cf53.record import Record, RecordType


def test_trivial_add():
    local_records = {
        Record(
            type=RecordType.a,
            name="example.com",
            content="1.2.3.4",
            ttl=3600,
            proxied=False,
            comment="test record",
        )
    }
    remote_records = set()

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone=local_records,
        remote_zone=remote_records,
    )

    assert len(diff.to_create) == 1
    assert len(diff.to_update) == 0
    assert len(diff.to_delete) == 0
    assert len(diff.in_sync) == 0
    created_record = next(iter(diff.to_create))
    assert created_record.type == RecordType.a
    assert created_record.name == "example.com"
    assert created_record.content == "1.2.3.4"
    assert created_record.ttl == 3600
    assert created_record.proxied is False
    assert created_record.comment == "test record"


def test_trivial_delete():
    local_records = set()
    remote_records = {
        Record(
            type=RecordType.a,
            name="example.com",
            content="1.2.3.4",
            ttl=3600,
            proxied=False,
            comment="test record",
            cloudflare_id="foo",
        )
    }

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone=local_records,
        remote_zone=remote_records,
    )

    assert len(diff.to_create) == 0
    assert len(diff.to_update) == 0
    assert len(diff.to_delete) == 1
    assert len(diff.in_sync) == 0
    delete_record = next(iter(diff.to_delete))
    assert delete_record.type == RecordType.a
    assert delete_record.name == "example.com"
    assert delete_record.content == "1.2.3.4"
    assert delete_record.ttl == 3600
    assert delete_record.proxied is False
    assert delete_record.comment == "test record"


def test_trivial_match_in_sync():
    matching_record = Record(
        type=RecordType.a,
        name="example.com",
        content="1.2.3.4",
        ttl=3600,
        proxied=False,
        comment="test record",
    )
    with_id = replace(
        matching_record,  # type: ignore[bad-argument-type]
        cloudflare_id="foo",
    )

    local_records = {matching_record}
    remote_records = {with_id}

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone=local_records,
        remote_zone=remote_records,
    )

    assert len(diff.to_create) == 0
    assert len(diff.to_update) == 0
    assert len(diff.to_delete) == 0
    assert len(diff.in_sync) == 1
    synced_record = next(iter(diff.in_sync))
    assert synced_record == with_id


def test_trivial_match_to_update():
    local_record = Record(
        type=RecordType.a,
        name="example.com",
        content="1.2.3.4",
        ttl=3600,
        proxied=False,
        comment="test record",
    )
    remote_record = replace(
        local_record,  # type: ignore[bad-argument-type]
        cloudflare_id="foo",
        comment="something else",
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_record},
        remote_zone={remote_record},
    )

    assert len(diff.to_create) == 0
    assert len(diff.to_update) == 1
    assert len(diff.to_delete) == 0
    assert len(diff.in_sync) == 0
    update = next(iter(diff.to_update))
    assert update.initial == remote_record
    assert update.desired == local_record
