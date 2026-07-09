# app/api/v1/users.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.user import (
    AdminUserListResponse,
    AdminUserOut,
    UserCreateIn,
    UserUpdateIn,
    to_admin_user_out,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.post("", response_model=AdminUserOut, status_code=201)
def create_user(body: UserCreateIn,
                db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> AdminUserOut:
    user = UserService(db).create_user(
        username=body.username, password=body.password,
        phone=body.phone, email=body.email, role_code=body.role_code,
    )
    return to_admin_user_out(user)


@router.get("", response_model=AdminUserListResponse)
def list_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               role: str | None = None, status: str | None = None,
               db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> AdminUserListResponse:
    res = UserService(db).list_users(page=page, page_size=page_size, role=role, status=status)
    return AdminUserListResponse(
        items=[to_admin_user_out(u) for u in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"],
    )


@router.get("/{user_id}", response_model=AdminUserOut)
def get_user(user_id: int, db: Session = Depends(get_db),
             _: User = Depends(require_role("admin"))) -> AdminUserOut:
    return to_admin_user_out(UserService(db).get_user(user_id))


@router.patch("/{user_id}", response_model=AdminUserOut)
def update_user(user_id: int, body: UserUpdateIn,
                db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> AdminUserOut:
    user = UserService(db).update_user(
        user_id, phone=body.phone, email=body.email,
        role_code=body.role_code, status=body.status, password=body.password,
    )
    return to_admin_user_out(user)
