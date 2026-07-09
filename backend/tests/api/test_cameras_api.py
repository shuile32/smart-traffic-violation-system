JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_create_device_requires_auth(client):
    assert client.post("/api/v1/admin/cameras", json={"device_code": "C1"}).status_code == 401


def test_create_device_reviewer_forbidden(client, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=reviewer_auth_headers)
    assert r.status_code == 403


def test_create_device_success(client, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/cameras",
                    json={"device_code": "CAM01", "location_text": "路口A"}, headers=admin_auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["device_code"] == "CAM01"
    assert data["status"] == "enabled"


def test_list_devices(client, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers)
    client.post("/api/v1/admin/cameras", json={"device_code": "C2"}, headers=admin_auth_headers)
    r = client.get("/api/v1/admin/cameras", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_get_device_404(client, admin_user, admin_auth_headers):
    assert client.get("/api/v1/admin/cameras/9999", headers=admin_auth_headers).status_code == 404


def test_patch_device(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    r = client.patch(f"/api/v1/admin/cameras/{dev_id}", json={"status": "disabled"}, headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "disabled"


def test_generate_key_returns_raw_once(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    r = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["raw_key"]
    assert data["key"]["status"] == "active"
    lst = client.get(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()["items"]
    assert "raw_key" not in lst[0]
    assert "key_hash" not in lst[0]


def test_revoke_key(client, admin_user, admin_auth_headers):
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    key_id = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()["key"]["id"]
    r = client.post(f"/api/v1/admin/cameras/{dev_id}/keys/{key_id}/revoke", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "revoked"


def test_revoked_key_fails_intake_auth(client, admin_user, admin_auth_headers, tmp_path, monkeypatch):
    """端到端：撤销 Key 后 /intakes/camera-captures 鉴权 401（张浩-7 + 张浩-9 衔接）。"""
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    dev_id = client.post("/api/v1/admin/cameras", json={"device_code": "C1"}, headers=admin_auth_headers).json()["id"]
    gen = client.post(f"/api/v1/admin/cameras/{dev_id}/keys", headers=admin_auth_headers).json()
    raw, key_id = gen["raw_key"], gen["key"]["id"]
    r1 = client.post("/api/v1/intakes/camera-captures", headers={"X-Camera-Key": raw},
                     files={"image": ("a.jpg", JPEG, "image/jpeg")}, data={"location_text": "A"})
    assert r1.status_code == 200
    client.post(f"/api/v1/admin/cameras/{dev_id}/keys/{key_id}/revoke", headers=admin_auth_headers)
    r2 = client.post("/api/v1/intakes/camera-captures", headers={"X-Camera-Key": raw},
                     files={"image": ("a.jpg", JPEG, "image/jpeg")}, data={"location_text": "A"})
    assert r2.status_code == 401
