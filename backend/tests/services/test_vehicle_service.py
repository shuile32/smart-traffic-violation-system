import pytest

from app.services.vehicle_service import VehicleService


def test_create_vehicle(db, citizen_user):
    v = VehicleService(db).create_vehicle(plate_no="粤A", owner_id=citizen_user.id, vehicle_type="小汽车", color="白")
    assert v.id is not None
    assert v.plate_no == "粤A"
    assert v.owner_id == citizen_user.id


def test_create_vehicle_duplicate_plate_409(db, citizen_user):
    VehicleService(db).create_vehicle(plate_no="粤A", owner_id=citizen_user.id, vehicle_type=None, color=None)
    with pytest.raises(Exception) as exc:
        VehicleService(db).create_vehicle(plate_no="粤A", owner_id=citizen_user.id, vehicle_type=None, color=None)
    assert exc.value.status_code == 409


def test_create_vehicle_bad_owner_400(db):
    with pytest.raises(Exception) as exc:
        VehicleService(db).create_vehicle(plate_no="粤A", owner_id=9999, vehicle_type=None, color=None)
    assert exc.value.status_code == 400


def test_list_vehicles_filter_by_plate(db, citizen_user):
    VehicleService(db).create_vehicle(plate_no="粤A123", owner_id=citizen_user.id, vehicle_type=None, color=None)
    VehicleService(db).create_vehicle(plate_no="粤B456", owner_id=citizen_user.id, vehicle_type=None, color=None)
    res = VehicleService(db).list_vehicles(page=1, page_size=20, plate_no="粤A")
    assert res["total"] == 1
    assert res["items"][0].plate_no == "粤A123"


def test_get_vehicle_404(db):
    with pytest.raises(Exception) as exc:
        VehicleService(db).get_vehicle(9999)
    assert exc.value.status_code == 404


def test_update_vehicle(db, citizen_user):
    v = VehicleService(db).create_vehicle(plate_no="粤A", owner_id=citizen_user.id, vehicle_type=None, color=None)
    u = VehicleService(db).update_vehicle(v.id, plate_no=None, owner_id=None, vehicle_type="卡车", color="红")
    assert u.vehicle_type == "卡车"
    assert u.color == "红"
