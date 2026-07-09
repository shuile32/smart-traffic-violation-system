JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_yolo_detect_requires_auth(client):
    resp = client.post(
        "/internal/ai/yolo/detect",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 401


def test_yolo_detect_citizen_forbidden(client, citizen_user, auth_headers):
    resp = client.post(
        "/internal/ai/yolo/detect",
        headers=auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 403


def test_yolo_detect_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/yolo/detect",
        headers=reviewer_auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_version"] == "stub-yolov8n"
    assert any(o["label"] == "car" for o in data["objects"])
    assert data["vehicle_bbox"] is not None


def test_ocr_plate_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/ocr/plate",
        headers=reviewer_auth_headers,
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["plate_no"] == "京A12345"


def test_ocr_plate_requires_auth(client):
    resp = client.post(
        "/internal/ai/ocr/plate",
        files={"image": ("a.jpg", JPEG, "image/jpeg")},
    )
    assert resp.status_code == 401
