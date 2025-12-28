from unittest.mock import MagicMock

from cf53.remote import load_remote_zones
import pytest


class AsyncMagicMock(MagicMock):
    """A MagicMock that can be awaited"""

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def mock_zone():
    mock_zone = MagicMock()
    mock_zone.name = "example.com"
    mock_zone.id = "test_zone_id"
    return mock_zone


def create_mock_record(
    name, content, comment, record_type="A", ttl=3600, proxied=False
):
    mock_record = MagicMock(
        spec=["type", "name", "content", "ttl", "proxied", "comment", "id"]
    )
    mock_record.type = record_type
    mock_record.name = name
    mock_record.content = content
    mock_record.ttl = ttl
    mock_record.proxied = proxied
    mock_record.comment = comment
    mock_record.id = f"record_{name.replace('.', '_')}"
    return mock_record


@pytest.fixture
def setup_mock_api(mock_client, mock_zone):
    def _setup(mock_records):
        mock_client.zones.list = AsyncMagicMock(return_value=[("result", [mock_zone])])
        mock_client.dns.records.list = AsyncMagicMock(
            return_value=[("result", mock_records)]
        )
        return mock_client

    return _setup


@pytest.mark.asyncio
async def test_ignore_comment_filters_records(mock_client, setup_mock_api):
    """Test that records with the ignore comment are filtered out"""

    records_to_ignore = [
        create_mock_record("example.com", "1.2.3.4", "managed-by = ddns"),
        create_mock_record("mail.example.com", "1.2.3.6", "managed-by = ddns"),
    ]
    records_to_keep = [
        create_mock_record("www.example.com", "1.2.3.5", "normal record", proxied=True),
    ]
    mock_client = setup_mock_api(records_to_ignore + records_to_keep)

    result = await load_remote_zones(
        client=mock_client, domains={"example.com"}, ignore_comment="managed-by = ddns"
    )

    assert len(result) == 1
    domain_key = ("example.com", "test_zone_id")
    assert domain_key in result
    records = result[domain_key]
    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    kept_record = next(iter(records))
    assert kept_record.name == "www.example.com"
    assert kept_record.comment == "normal record"
    assert kept_record.proxied


@pytest.mark.asyncio
async def test_ignore_comment_no_filter_when_empty(mock_client, setup_mock_api):
    records = [
        create_mock_record("example.com", "1.2.3.4", "managed-by = ddns"),
        create_mock_record("www.example.com", "1.2.3.5", "normal record", proxied=True),
    ]
    mock_client = setup_mock_api(records)

    result = await load_remote_zones(
        client=mock_client,
        domains={"example.com"},
        ignore_comment="",  # Empty string should not filter anything
    )

    assert len(result) == 1
    domain_key = ("example.com", "test_zone_id")
    assert domain_key in result
    records_result = result[domain_key]
    assert len(records_result) == 2, f"Expected 2 records, got {len(records_result)}"
    record_names = {record.name for record in records_result}
    assert "example.com" in record_names
    assert "www.example.com" in record_names


@pytest.mark.asyncio
async def test_ignore_comment_no_filter_when_not_specified(mock_client, setup_mock_api):
    records = [
        create_mock_record("example.com", "1.2.3.4", "managed-by = ddns"),
    ]
    mock_client = setup_mock_api(records)
    result = await load_remote_zones(
        client=mock_client,
        domains={"example.com"},
    )

    assert len(result) == 1
    domain_key = ("example.com", "test_zone_id")
    assert domain_key in result
    records_result = result[domain_key]
    assert len(records_result) == 1, f"Expected 1 record, got {len(records_result)}"
    kept_record = next(iter(records_result))
    assert kept_record.name == "example.com"
    assert kept_record.comment == "managed-by = ddns"
