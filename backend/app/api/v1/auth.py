# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.auth import (
    LoginRequest, MenusOut, PasswordChangeRequest, ProfileUpdateRequest,
    RegisterRequest, TokenResponse, UserOut)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已禁用")
    token = create_access_token(subject=str(user.id), role=user.role.code)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, username=user.username, role_code=user.role.code),
    )


ROLE_MENUS: dict[str, list[str]] = {
    "citizen": ["citizen_report", "my_violations"],
    "reviewer": ["review_workbench", "violations_query"],
    "admin": ["review_workbench", "violations_query", "system_management", "statistics"],
    "camera": [],
}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, username=user.username, role_code=user.role.code)


permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permissions_router.get("/menus", response_model=MenusOut)
def menus(user: User = Depends(get_current_user)) -> MenusOut:
    return MenusOut(menus=ROLE_MENUS.get(user.role.code, []))


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    role = db.query(Role).filter(Role.code == "citizen").first()
    if role is None:
        raise HTTPException(status_code=500, detail="系统未初始化角色")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        phone=body.phone,
        email=body.email,
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role.code)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, username=user.username, role_code=user.role.code),
    )


@router.put("/profile", response_model=UserOut)
def update_profile(body: ProfileUpdateRequest, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> UserOut:
    if body.phone is not None:
        user.phone = body.phone
    if body.email is not None:
        user.email = body.email
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, role_code=user.role.code)


@router.put("/password")
def change_password(body: PasswordChangeRequest, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "密码修改成功"}
