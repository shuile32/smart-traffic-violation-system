# tests/api/test_intakes.py
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_citizen_upload_success(client, citizen_user, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_no"].startswith("CASE")
    assert data["status"] == "uploaded"


def test_citizen_upload_requires_auth(client):
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 401


def test_citizen_upload_duplicate(client, citizen_user, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    response = client.post(
        "/api/v1/intakes/citizen-reports",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口A"},
    )
    assert response.status_code == 409


def test_camera_capture_success(client, camera_key, tmp_path, monkeypatch):
    raw_key, _ = camera_key
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": raw_key},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B", "speed": "88"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_no"].startswith("CASE")


def test_camera_capture_bad_key(client):
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": "wrong"},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B"},
    )
    assert response.status_code == 401


def test_camera_capture_disabled_device(client, camera_device, camera_key, db, tmp_path, monkeypatch):
    raw_key, _ = camera_key
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    camera_device.status = "disabled"
    db.commit()
    response = client.post(
        "/api/v1/intakes/camera-captures",
        headers={"X-Camera-Key": raw_key},
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
        data={"location_text": "路口B"},
    )
    assert response.status_code == 401
