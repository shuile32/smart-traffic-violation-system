from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.vehicle import VehicleCreateIn, VehicleListResponse, VehicleOut, VehicleUpdateIn
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/admin/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleOut, status_code=201)
def create_vehicle(body: VehicleCreateIn,
                   db: Session = Depends(get_db),
                   _: User = Depends(require_role("admin"))) -> VehicleOut:
    v = VehicleService(db).create_vehicle(
        plate_no=body.plate_no, owner_id=body.owner_id,
        vehicle_type=body.vehicle_type, color=body.color)
    return VehicleOut.model_validate(v)


@router.get("", response_model=VehicleListResponse)
def list_vehicles(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  plate_no: str | None = None,
                  db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))) -> VehicleListResponse:
    res = VehicleService(db).list_vehicles(page=page, page_size=page_size, plate_no=plate_no)
    return VehicleListResponse(
        items=[VehicleOut.model_validate(v) for v in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"])


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))) -> VehicleOut:
    return VehicleOut.model_validate(VehicleService(db).get_vehicle(vehicle_id))


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, body: VehicleUpdateIn,
                   db: Session = Depends(get_db),
                   _: User = Depends(require_role("admin"))) -> VehicleOut:
    v = VehicleService(db).update_vehicle(
        vehicle_id, plate_no=body.plate_no, owner_id=body.owner_id,
        vehicle_type=body.vehicle_type, color=body.color)
    return VehicleOut.model_validate(v)
