from datetime import datetime

from pydantic import BaseModel


class CameraDeviceOut(BaseModel):
    id: int
    device_code: str
    location_text: str | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CameraDeviceCreateIn(BaseModel):
    device_code: str
    location_text: str | None = None


class CameraDeviceUpdateIn(BaseModel):
    location_text: str | None = None
    status: str | None = None  # enabled / disabled


class CameraDeviceListResponse(BaseModel):
    items: list[CameraDeviceOut]
    total: int
    page: int
    page_size: int


class CameraKeyOut(BaseModel):
    id: int
    camera_device_id: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
    # 不含 key_hash / raw


class CameraKeyCreateOut(BaseModel):
    raw_key: str  # 只在生成时返回一次
    key: CameraKeyOut


class CameraKeyListResponse(BaseModel):
    items: list[CameraKeyOut]
