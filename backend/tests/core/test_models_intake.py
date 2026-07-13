# tests/core/test_models_intake.py
from app.models.intake import CameraApiKey, CameraDevice, Case, IntakeEvent, MediaAsset
from sqlalchemy import Text


def test_create_intake_and_case(db):
    event = IntakeEvent(
        source_type="citizen", source_id=1, location_text="路口A", image_hash="abc",
    )
    db.add(event)
    db.commit()
    case = Case(case_no="CASE20260708000001", intake_event_id=event.id, status="uploaded")
    db.add(case)
    db.commit()
    media = MediaAsset(intake_event_id=event.id, asset_type="original", url="/media/x.jpg", mime_type="image/jpeg", size=1024)
    db.add(media)
    db.commit()
    assert case.id is not None
    assert case.intake_event.image_hash == "abc"


def test_create_camera_and_key(db):
    dev = CameraDevice(device_code="CAM01", location_text="路口B")
    db.add(dev)
    db.commit()
    key = CameraApiKey(camera_device_id=dev.id, key_hash="hashed")
    db.add(key)
    db.commit()
    assert key.id is not None


def test_case_ai_result_uses_text_storage_for_multi_target_evidence():
    assert isinstance(Case.__table__.c.ai_result_json.type, Text)
