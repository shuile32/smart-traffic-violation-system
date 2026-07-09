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


def test_rules_evaluate_speed_matched(client, reviewer_user, reviewer_auth_headers):
    body = {
        "detection": {"objects": [], "vehicle_bbox": None, "plate_bbox": None, "annotated_image_url": None, "model_version": ""},
        "ocr_result": "京A12345",
        "intake_event": {"speed": 120},
        "rule": {"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    }
    resp = client.post("/internal/ai/rules/evaluate", headers=reviewer_auth_headers, json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_matched"] is True
    assert data["evidence_level"] == "complete"


def test_rules_evaluate_requires_auth(client):
    resp = client.post("/internal/ai/rules/evaluate", json={})
    assert resp.status_code == 401


def test_review_text_success(client, reviewer_user, reviewer_auth_headers):
    resp = client.post(
        "/internal/ai/review/text",
        headers=reviewer_auth_headers,
        json={"evidence": "any"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conclusion"] == "suggest_approve"
    assert data["ai_confidence"] == 0.88


def test_review_text_citizen_forbidden(client, citizen_user, auth_headers):
    resp = client.post("/internal/ai/review/text", headers=auth_headers, json={})
    assert resp.status_code == 403
