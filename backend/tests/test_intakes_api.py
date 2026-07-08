"""intakes 路由测试：citizen-reports / camera-captures / admin-uploads。"""


def _jpg():
    # 最小 JPEG 字节流
    return ("test.jpg",
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9",
            "image/jpeg")


def test_citizen_report_no_token_returns_401(client):
    resp = client.post("/api/v1/intakes/citizen-reports",
                       files={"image": _jpg()},
                       data={"location_text": "A", "captured_at": "2026-07-08T10:00:00"})
    assert resp.status_code == 401


def test_citizen_report_success(client, make_user, auth_header, monkeypatch, tmp_path,
                               db_session, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="citizen")
    resp = client.post("/api/v1/intakes/citizen-reports",
                       files={"image": _jpg()},
                       data={"location_text": "路口A",
                             "captured_at": "2026-07-08T10:00:00",
                             "description": "违停"},
                       headers=auth_header("citizen", u.id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "uploaded"
    assert data["case_no"].startswith("CASE")
    from app.models.case import Case
    assert db_session.query(Case).count() == 1
    assert any(c[0] == "chain" for c in celery_calls)


def test_camera_capture_no_key_returns_401(client):
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001", "captured_at": "2026-07-08T10:00:00"})
    assert resp.status_code == 401


def test_camera_capture_invalid_key_returns_401(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001", "captured_at": "2026-07-08T10:00:00"},
                       headers={"X-Camera-Key": "wrong"})
    assert resp.status_code == 401


def test_camera_capture_success(client, seed_camera, monkeypatch, tmp_path, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    resp = client.post("/api/v1/intakes/camera-captures",
                       files={"image": _jpg()},
                       data={"camera_id": "DEV001",
                             "captured_at": "2026-07-08T10:00:00",
                             "speed": "88.5"},
                       headers={"X-Camera-Key": seed_camera["raw_key"]})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "uploaded"
    assert any(c[0] == "chain" for c in celery_calls)


def test_admin_upload_citizen_forbidden(client, make_user, auth_header, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="citizen")
    resp = client.post("/api/v1/intakes/admin-uploads",
                       files={"image": _jpg()},
                       data={"captured_at": "2026-07-08T10:00:00"},
                       headers=auth_header("citizen", u.id))
    assert resp.status_code == 403


def test_admin_upload_reviewer_success(client, make_user, auth_header, monkeypatch,
                                      tmp_path, celery_calls):
    monkeypatch.setattr("app.api.v1.intakes.MEDIA_DIR", str(tmp_path))
    u = make_user(role="reviewer")
    resp = client.post("/api/v1/intakes/admin-uploads",
                       files={"image": _jpg()},
                       data={"captured_at": "2026-07-08T10:00:00", "location_text": "B"},
                       headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert any(c[0] == "chain" for c in celery_calls)
