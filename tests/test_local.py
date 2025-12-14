from cf53 import Record, RecordType, load_zones_dir

single_record_content = """
[[a]]
name = "example.com"
content = "127.0.0.1"
"""

single_record_expected = {
    Record(
        type=RecordType.a,
        name="example.com",
        content="127.0.0.1",
        ttl=1,
        proxied=False,
        comment="",
    )
}


many_records_content = """
[[a]]
name = "example.net"
content = "192.168.1.1"
ttl=500

[[a]]
name = "foo.example.net"
content = "192.168.1.1"
proxied = true
comment = "for foo"

[[aaaa]]
name = "example.net"
content = "2001:db8::1"

[[cname]]
name = "www"
content = "example.net"

[[txt]]
name = "example.net"
content = "v=spf1 include:_spf.google.com ~all"

[[mx]]
name = "example.net"
content = "mail.example.net"
priority = 10
"""

many_records_expected = {
    Record(
        type=RecordType.a,
        name="example.net",
        content="192.168.1.1",
        ttl=500,
        proxied=False,
        comment="",
    ),
    Record(
        type=RecordType.a,
        name="foo.example.net",
        content="192.168.1.1",
        ttl=1,
        proxied=True,
        comment="for foo",
    ),
    Record(
        type=RecordType.aaaa,
        name="example.net",
        content="2001:db8::1",
        ttl=1,
        proxied=False,
        comment="",
    ),
    Record(
        type=RecordType.cname,
        name="www.example.net",
        content="example.net",
        ttl=1,
        proxied=False,
        comment="",
    ),
    Record(
        type=RecordType.txt,
        name="example.net",
        content='"v=spf1 include:_spf.google.com ~all"',
        ttl=1,
        proxied=False,
        comment="",
    ),
    Record(
        type=RecordType.mx,
        name="example.net",
        content="mail.example.net",
        ttl=1,
        proxied=False,
        comment="",
        priority=10,
    ),
}

denormalized_name_records = """
[[a]]
name = "@"
content = "127.0.0.1"

[[txt]]
name = "_dmarc"
content = "v=DMARC1; p=quarantine;"
"""

denormalized_name_expected = {
    Record(
        type=RecordType.a,
        name="example.org",
        content="127.0.0.1",
        ttl=1,
        proxied=False,
        comment="",
    ),
    Record(
        type=RecordType.txt,
        name="_dmarc.example.org",
        content='"v=DMARC1; p=quarantine;"',
        ttl=1,
        proxied=False,
        comment="",
    ),
}

default_comment_records = """
[[a]]
name = "example.ca"
content = "1.2.3.4"
comment = "domain apex"
[[a]]
name = "foo.example.ca"
content = "1.2.3.4"
"""

default_comment_expected = {
    Record(
        type=RecordType.a,
        name="example.ca",
        content="1.2.3.4",
        ttl=1,
        proxied=False,
        comment="domain apex",
    ),
    Record(
        type=RecordType.a,
        name="foo.example.ca",
        content="1.2.3.4",
        ttl=1,
        proxied=False,
        comment="default comment",
    ),
}


def test_empty(build_zones_dir):
    zones_dir = build_zones_dir({"example.com.toml": ""})
    zones = load_zones_dir(zones_dir=zones_dir)
    assert zones == {"example.com": set()}


def test_single_record(build_zones_dir):
    zones_dir = build_zones_dir({"example.com.toml": single_record_content})
    zones = load_zones_dir(zones_dir=zones_dir)
    assert zones == {"example.com": single_record_expected}


def test_many_records(build_zones_dir):
    zones_dir = build_zones_dir({"example.net.toml": many_records_content})
    zones = load_zones_dir(zones_dir=zones_dir)
    assert zones == {"example.net": many_records_expected}


def test_denormalized_names(build_zones_dir):
    zones_dir = build_zones_dir({"example.org.toml": denormalized_name_records})
    zones = load_zones_dir(zones_dir=zones_dir)
    assert zones == {"example.org": denormalized_name_expected}


def test_many_zone_files(build_zones_dir):
    zones_dir = build_zones_dir(
        {
            "example.com.toml": single_record_content,
            "example.net.toml": many_records_content,
            "example.org.toml": denormalized_name_records,
        }
    )
    zones = load_zones_dir(zones_dir=zones_dir)
    assert zones == {
        "example.com": single_record_expected,
        "example.net": many_records_expected,
        "example.org": denormalized_name_expected,
    }


def test_default_comment(build_zones_dir):
    zones_dir = build_zones_dir({"example.ca.toml": default_comment_records})
    zones = load_zones_dir(zones_dir=zones_dir, default_comment="default comment")
    assert zones == {"example.ca": default_comment_expected}


def test_domain_seletion(build_zones_dir):
    zones_dir = build_zones_dir(
        {
            "example.net.toml": many_records_content,
            "example.ca.toml": default_comment_records,
        }
    )
    zones = load_zones_dir(
        zones_dir=zones_dir,
        only_domains={"example.net"},
    )
    assert zones == {"example.net": many_records_expected}
