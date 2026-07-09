# app/api/v1/cameras.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.camera import (
    CameraDeviceCreateIn,
    CameraDeviceListResponse,
    CameraDeviceOut,
    CameraDeviceUpdateIn,
    CameraKeyCreateOut,
    CameraKeyListResponse,
    CameraKeyOut,
)
from app.services.camera_service import CameraService

router = APIRouter(prefix="/admin/cameras", tags=["cameras"])


@router.post("", response_model=CameraDeviceOut, status_code=201)
def create_device(body: CameraDeviceCreateIn,
                  db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    dev = CameraService(db).create_device(device_code=body.device_code, location_text=body.location_text)
    return CameraDeviceOut.model_validate(dev)


@router.get("", response_model=CameraDeviceListResponse)
def list_devices(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 db: Session = Depends(get_db),
                 _: User = Depends(require_role("admin"))) -> CameraDeviceListResponse:
    res = CameraService(db).list_devices(page=page, page_size=page_size)
    return CameraDeviceListResponse(
        items=[CameraDeviceOut.model_validate(d) for d in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"],
    )


@router.get("/{device_id}", response_model=CameraDeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    return CameraDeviceOut.model_validate(CameraService(db).get_device(device_id))


@router.patch("/{device_id}", response_model=CameraDeviceOut)
def update_device(device_id: int, body: CameraDeviceUpdateIn,
                  db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))) -> CameraDeviceOut:
    dev = CameraService(db).update_device(device_id, location_text=body.location_text, status=body.status)
    return CameraDeviceOut.model_validate(dev)


@router.post("/{device_id}/keys", response_model=CameraKeyCreateOut, status_code=201)
def create_key(device_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraKeyCreateOut:
    raw, key = CameraService(db).create_key(device_id)
    return CameraKeyCreateOut(raw_key=raw, key=CameraKeyOut.model_validate(key))


@router.get("/{device_id}/keys", response_model=CameraKeyListResponse)
def list_keys(device_id: int, db: Session = Depends(get_db),
              _: User = Depends(require_role("admin"))) -> CameraKeyListResponse:
    keys = CameraService(db).list_keys(device_id)
    return CameraKeyListResponse(items=[CameraKeyOut.model_validate(k) for k in keys])


@router.post("/{device_id}/keys/{key_id}/revoke", response_model=CameraKeyOut)
def revoke_key(device_id: int, key_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> CameraKeyOut:
    key = CameraService(db).revoke_key(device_id, key_id)
    return CameraKeyOut.model_validate(key)
