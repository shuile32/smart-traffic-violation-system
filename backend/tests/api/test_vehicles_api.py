def test_create_vehicle_requires_auth(client, citizen_user):
    assert client.post("/api/v1/admin/vehicles",
                       json={"plate_no": "粤A", "owner_id": citizen_user.id}).status_code == 401


def test_create_vehicle_reviewer_forbidden(client, citizen_user, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/admin/vehicles", headers=reviewer_auth_headers,
                    json={"plate_no": "粤A", "owner_id": citizen_user.id})
    assert r.status_code == 403


def test_create_vehicle_success(client, citizen_user, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/vehicles", headers=admin_auth_headers, json={
        "plate_no": "粤A123", "owner_id": citizen_user.id, "vehicle_type": "小汽车", "color": "白"})
    assert r.status_code == 201
    data = r.json()
    assert data["plate_no"] == "粤A123"
    assert data["vehicle_type"] == "小汽车"


def test_list_vehicles(client, citizen_user, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                json={"plate_no": "粤A", "owner_id": citizen_user.id})
    client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                json={"plate_no": "粤B", "owner_id": citizen_user.id})
    r = client.get("/api/v1/admin/vehicles", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 2


def test_get_vehicle_404(client, admin_user, admin_auth_headers):
    assert client.get("/api/v1/admin/vehicles/9999", headers=admin_auth_headers).status_code == 404


def test_patch_vehicle(client, citizen_user, admin_user, admin_auth_headers):
    vid = client.post("/api/v1/admin/vehicles", headers=admin_auth_headers,
                      json={"plate_no": "粤A", "owner_id": citizen_user.id}).json()["id"]
    r = client.patch(f"/api/v1/admin/vehicles/{vid}", headers=admin_auth_headers,
                     json={"vehicle_type": "卡车", "color": "红"})
    assert r.status_code == 200
    data = r.json()
    assert data["vehicle_type"] == "卡车"
    assert data["color"] == "红"
