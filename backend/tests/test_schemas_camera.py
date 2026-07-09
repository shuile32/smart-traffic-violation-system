from datetime import datetime, timezone

from app.schemas.camera import (
    CameraDeviceCreateIn,
    CameraDeviceListResponse,
    CameraDeviceOut,
    CameraDeviceUpdateIn,
    CameraKeyCreateOut,
    CameraKeyListResponse,
    CameraKeyOut,
)


def test_camera_device_out_from_attributes():
    d = CameraDeviceOut.model_validate({
        "id": 1, "device_code": "C1", "location_text": "A",
        "status": "enabled", "created_at": datetime(2026, 7, 8, tzinfo=timezone.utc),
    })
    assert d.device_code == "C1"
    assert d.status == "enabled"


def test_camera_device_create_in_defaults():
    c = CameraDeviceCreateIn(device_code="C1")
    assert c.location_text is None


def test_camera_device_update_in_all_optional():
    u = CameraDeviceUpdateIn()
    assert u.location_text is None
    assert u.status is None


def test_camera_key_create_out():
    o = CameraKeyCreateOut(raw_key="abc", key=CameraKeyOut(
        id=1, camera_device_id=2, status="active",
        created_at=datetime(2026, 7, 8, tzinfo=timezone.utc)))
    assert o.raw_key == "abc"
    assert o.key.id == 1


def test_list_responses():
    lr = CameraDeviceListResponse(items=[], total=0, page=1, page_size=20)
    assert lr.total == 0
    kr = CameraKeyListResponse(items=[])
    assert kr.items == []
