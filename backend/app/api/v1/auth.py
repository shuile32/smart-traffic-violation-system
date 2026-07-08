"""认证路由"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, verify_password, create_access_token
from app.core.permissions import get_menus_for_role
from app.models.user import User
from app.models.audit_log import AuditLog
from schemas.common import APIResponse
from schemas.auth import LoginRequest

router = APIRouter()


@router.post("/login", response_model=APIResponse[dict])
async def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not verify_password(body.password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(401, detail="用户名或密码错误")

    if user.status == 0:
        from fastapi import HTTPException
        raise HTTPException(403, detail="账号已被禁用")

    role_name = user.role.name if user.role else "citizen"
    token = create_access_token(user.id, role_name)

    # 审计日志
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action="login",
        target_type="user",
        target_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return APIResponse(data={
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict(),
    })


@router.get("/me", response_model=APIResponse[dict])
async def get_me(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(404, detail="用户不存在")
    return APIResponse(data=user.to_dict())


@router.get("/permissions/menus", response_model=APIResponse[dict])
async def get_menus(payload: dict = Depends(get_current_user)):
    role = payload.get("role", "citizen")
    menus = get_menus_for_role(role)
    return APIResponse(data={"menus": menus})
