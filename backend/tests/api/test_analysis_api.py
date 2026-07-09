def test_generate_report_success(client, reviewer_user, reviewer_auth_headers):
    r = client.post("/api/v1/analysis/reports", headers=reviewer_auth_headers, json={
        "start_time": "2026-01-01", "end_time": "2026-07-01", "report_type": "综合"})
    assert r.status_code == 200
    data = r.json()
    assert "title" in data
    assert "content" in data
    assert data["author"] == "AI 分析助手 (stub)"


def test_generate_report_requires_auth(client):
    assert client.post("/api/v1/analysis/reports", json={}).status_code == 401


def test_generate_report_citizen_forbidden(client, citizen_user, auth_headers):
    r = client.post("/api/v1/analysis/reports", headers=auth_headers, json={})
    assert r.status_code == 403
