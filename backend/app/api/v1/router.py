# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1 import auth, cases, intakes, violations
from app.api.v1.auth import permissions_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(permissions_router)
api_router.include_router(intakes.router)
api_router.include_router(cases.router)
api_router.include_router(violations.router)
