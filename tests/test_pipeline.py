import pytest
from src.schemas import RawDeviceAsset
from src.normalizer import reconcile_and_normalize, normalize_manufacturer

def test_raw_device_asset_validation():
    # Deve passar e limpar espaços / maiúsculas
    raw = {
        "device_id": "TEST-1",
        "serial_number": " abc123xyz ",
        "hostname": " HOST-TEST ",
        "manufacturer": "Dell",
        "model": "XPS 13",
        "os_name": "Windows 11",
        "os_version": "23H2",
        "last_checkin": "2026-09-30T10:00:00"
    }
    asset = RawDeviceAsset(**raw)
    assert asset.serial_number == "ABC123XYZ"
    assert asset.hostname == "host-test"

def test_invalid_serial_number():
    raw = {
        "device_id": "TEST-2",
        "serial_number": "UNKNOWN",
        "hostname": "bad-host",
        "manufacturer": "Dell",
        "model": "XPS 13",
        "os_name": "Windows 11",
        "os_version": "23H2",
        "last_checkin": "2026-09-30T10:00:00"
    }
    with pytest.raises(ValueError):
        RawDeviceAsset(**raw)

def test_deduplication_keeps_latest_record():
    assets = [
        {
            "device_id": "OLD-1",
            "serial_number": "SAME-SERIAL",
            "hostname": "host-antigo",
            "manufacturer": "DELL INC.",
            "last_checkin": "2026-09-01T10:00:00"
        },
        {
            "device_id": "NEW-1",
            "serial_number": "SAME-SERIAL",
            "hostname": "host-novo",
            "manufacturer": "Dell",
            "last_checkin": "2026-09-30T10:00:00"
        }
    ]
    cis = reconcile_and_normalize(assets)
    assert len(cis) == 1
    assert cis[0].name == "host-novo"
    assert cis[0].manufacturer == "Dell"
