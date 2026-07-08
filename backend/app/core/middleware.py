"""摄像头 API Key 鉴权 — 第一阶段简化版：只校验 X-Camera-Key

签名 + 时间戳防重放推迟到后续阶段。
"""

import hashlib

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db


async def verify_camera_auth(request: Request, db: Session = Depends(get_db)) -> int:
    """校验摄像头 API Key，返回 camera_device_id"""

    api_key = request.headers.get("X-Camera-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-Camera-Key 鉴权头",
        )

    from app.models.camera_api_key import CameraApiKey

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    camera_key = (
        db.query(CameraApiKey)
        .filter(CameraApiKey.key_hash == key_hash, CameraApiKey.status == "active")
        .first()
    )

    if not camera_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 API Key")

    return camera_key.camera_device_id
