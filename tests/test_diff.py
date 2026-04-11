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


def test_mx_priority_change():
    local_record = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server",
        priority=10,
    )
    remote_record = replace(
        local_record,
        cloudflare_id="foo",
        priority=20,
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_record},
        remote_zone={remote_record},
    )

    assert len(diff.to_update) == 1
    update = next(iter(diff.to_update))
    assert update.initial.priority == 20
    assert update.desired.priority == 10


def test_ttl_change():
    local_record = Record(
        type=RecordType.a,
        name="example.com",
        content="1.2.3.4",
        ttl=3600,
        proxied=False,
        comment="test",
    )
    remote_record = replace(
        local_record,
        cloudflare_id="foo",
        ttl=1800,
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_record},
        remote_zone={remote_record},
    )

    assert len(diff.to_update) == 1
    update = next(iter(diff.to_update))
    assert update.initial.ttl == 1800
    assert update.desired.ttl == 3600


def test_proxied_toggle():
    local_record = Record(
        type=RecordType.a,
        name="example.com",
        content="1.2.3.4",
        ttl=3600,
        proxied=True,
        comment="test",
    )
    remote_record = replace(
        local_record,
        cloudflare_id="foo",
        proxied=False,
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_record},
        remote_zone={remote_record},
    )

    assert len(diff.to_update) == 1
    update = next(iter(diff.to_update))
    assert update.initial.proxied is False
    assert update.desired.proxied is True


def test_comment_change():
    local_record = Record(
        type=RecordType.a,
        name="example.com",
        content="1.2.3.4",
        ttl=3600,
        proxied=False,
        comment="new comment",
    )
    remote_record = replace(
        local_record,
        cloudflare_id="foo",
        comment="old comment",
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_record},
        remote_zone={remote_record},
    )

    assert len(diff.to_update) == 1
    update = next(iter(diff.to_update))
    assert update.initial.comment == "old comment"
    assert update.desired.comment == "new comment"


def test_complex_mx_priority_changes():
    # Remote records
    remote_mx_10 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail1.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 1",
        priority=10,
        cloudflare_id="mx1",
    )
    remote_mx_20 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail2.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 2",
        priority=20,
        cloudflare_id="mx2",
    )
    remote_mx_30 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail3.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 3",
        priority=30,
        cloudflare_id="mx3",
    )

    # Local records
    local_mx_10 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail1.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 1",
        priority=10,
    )
    local_mx_30 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail3.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 3",
        priority=30,
    )
    local_mx_21 = Record(
        type=RecordType.mx,
        name="example.com",
        content="mail4.example.com",
        ttl=3600,
        proxied=False,
        comment="mail server 4",
        priority=21,
    )

    diff = Diff.from_zones(
        domain="example.com",
        zone_id="test_zone_id",
        local_zone={local_mx_10, local_mx_30, local_mx_21},
        remote_zone={remote_mx_10, remote_mx_20, remote_mx_30},
    )

    # Verify: 1 create (priority 21), 1 delete (priority 20), 2 in_sync (10, 30)
    assert len(diff.to_create) == 1
    assert len(diff.to_delete) == 1
    assert len(diff.to_update) == 0
    assert len(diff.in_sync) == 2

    # Check specific records
    created = next(iter(diff.to_create))
    assert created.priority == 21
    assert created.content == "mail4.example.com"

    deleted = next(iter(diff.to_delete))
    assert deleted.priority == 20
    assert deleted.content == "mail2.example.com"

    in_sync_records = {r.content for r in diff.in_sync}
    assert "mail1.example.com" in in_sync_records
    assert "mail3.example.com" in in_sync_records
