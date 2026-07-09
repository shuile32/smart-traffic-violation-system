# app/services/camera_service.py
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.intake import CameraApiKey, CameraDevice

VALID_DEVICE_STATUS = {"enabled", "disabled"}


class CameraService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_device(self, *, device_code: str, location_text: str | None) -> CameraDevice:
        if self.db.query(CameraDevice).filter_by(device_code=device_code).first():
            raise HTTPException(status_code=409, detail="设备编号已存在")
        dev = CameraDevice(device_code=device_code, location_text=location_text)
        self.db.add(dev)
        self.db.commit()
        self.db.refresh(dev)
        return dev

    def list_devices(self, *, page: int, page_size: int) -> dict:
        total = self.db.query(CameraDevice).count()
        items = (
            self.db.query(CameraDevice)
            .order_by(CameraDevice.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_device(self, device_id: int) -> CameraDevice:
        dev = self.db.get(CameraDevice, device_id)
        if dev is None:
            raise HTTPException(status_code=404, detail="设备不存在")
        return dev

    def update_device(self, device_id: int, *, location_text: str | None, status: str | None) -> CameraDevice:
        dev = self.get_device(device_id)
        if status is not None and status not in VALID_DEVICE_STATUS:
            raise HTTPException(status_code=400, detail="status 必须是 enabled 或 disabled")
        if location_text is not None:
            dev.location_text = location_text
        if status is not None:
            dev.status = status
        self.db.commit()
        self.db.refresh(dev)
        return dev

    def create_key(self, device_id: int) -> tuple[str, CameraApiKey]:
        dev = self.get_device(device_id)  # 404 if not exist
        raw = secrets.token_urlsafe(32)
        key = CameraApiKey(
            camera_device_id=dev.id,
            key_hash=hashlib.sha256(raw.encode()).hexdigest(),
        )
        self.db.add(key)
        self.db.commit()
        self.db.refresh(key)
        return raw, key

    def list_keys(self, device_id: int) -> list[CameraApiKey]:
        self.get_device(device_id)  # 404 if device not exist
        return (
            self.db.query(CameraApiKey)
            .filter(CameraApiKey.camera_device_id == device_id)
            .order_by(CameraApiKey.id.desc())
            .all()
        )

    def revoke_key(self, device_id: int, key_id: int) -> CameraApiKey:
        self.get_device(device_id)
        key = (
            self.db.query(CameraApiKey)
            .filter(CameraApiKey.id == key_id, CameraApiKey.camera_device_id == device_id)
            .first()
        )
        if key is None:
            raise HTTPException(status_code=404, detail="Key 不存在")
        key.status = "revoked"
        self.db.commit()
        self.db.refresh(key)
        return key
