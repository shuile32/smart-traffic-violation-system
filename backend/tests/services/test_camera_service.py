import hashlib

import pytest

from app.models.intake import CameraApiKey
from app.services.camera_service import CameraService


def test_create_device(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text="路口A")
    assert dev.id is not None
    assert dev.device_code == "CAM01"
    assert dev.status == "enabled"


def test_create_device_duplicate_409(db):
    CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).create_device(device_code="CAM01", location_text=None)
    assert exc.value.status_code == 409


def test_list_devices_pagination(db):
    for i in range(5):
        CameraService(db).create_device(device_code=f"CAM0{i}", location_text=None)
    res = CameraService(db).list_devices(page=1, page_size=2)
    assert res["total"] == 5
    assert len(res["items"]) == 2


def test_get_device_404(db):
    with pytest.raises(Exception) as exc:
        CameraService(db).get_device(9999)
    assert exc.value.status_code == 404


def test_update_device(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text="A")
    updated = CameraService(db).update_device(dev.id, location_text="B", status="disabled")
    assert updated.location_text == "B"
    assert updated.status == "disabled"


def test_update_device_invalid_status_400(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).update_device(dev.id, location_text=None, status="bogus")
    assert exc.value.status_code == 400


def test_create_key_returns_raw_and_sha256_hash(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    raw, key = CameraService(db).create_key(dev.id)
    assert len(raw) > 0
    assert key.key_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert key.status == "active"


def test_create_key_device_not_found_404(db):
    with pytest.raises(Exception) as exc:
        CameraService(db).create_key(9999)
    assert exc.value.status_code == 404


def test_revoke_key(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    _, key = CameraService(db).create_key(dev.id)
    revoked = CameraService(db).revoke_key(dev.id, key.id)
    assert revoked.status == "revoked"


def test_revoke_key_not_found_404(db):
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    with pytest.raises(Exception) as exc:
        CameraService(db).revoke_key(dev.id, 9999)
    assert exc.value.status_code == 404


def test_revoked_key_not_in_active_query(db):
    """撤销后的 Key 在张浩-9 的 active 查询里查不到（鉴权会 401）。"""
    dev = CameraService(db).create_device(device_code="CAM01", location_text=None)
    raw, key = CameraService(db).create_key(dev.id)
    CameraService(db).revoke_key(dev.id, key.id)
    found = (
        db.query(CameraApiKey)
        .filter(
            CameraApiKey.key_hash == hashlib.sha256(raw.encode()).hexdigest(),
            CameraApiKey.status == "active",
        )
        .first()
    )
    assert found is None
