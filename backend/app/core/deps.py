# app/core/deps.py
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token, verify_password
from app.models.intake import CameraApiKey, CameraDevice
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="无效的令牌")
    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.code not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return checker


def get_camera_device(
    x_camera_key: str = Header(..., alias="X-Camera-Key"),
    db: Session = Depends(get_db),
) -> CameraDevice:
    keys = db.query(CameraApiKey).filter(CameraApiKey.status == "active").all()
    for k in keys:
        if verify_password(x_camera_key, k.key_hash):
            dev = db.get(CameraDevice, k.camera_device_id)
            if dev and dev.status == "enabled":
                return dev
    raise HTTPException(status_code=401, detail="无效的摄像头密钥")


from app.services.notification_provider import EmailSmtpProvider, NotificationProvider


def get_notification_provider() -> NotificationProvider:
    return EmailSmtpProvider()
