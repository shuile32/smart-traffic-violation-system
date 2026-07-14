import pytest

from app.models.violation_rule import ViolationRule


def test_create_rule_success(client, admin_user, admin_auth_headers):
    r = client.post("/api/v1/admin/rules", headers=admin_auth_headers, json={
        "rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed",
        "params": '{"speed_limit": 80}', "description": "限速80"})
    assert r.status_code == 201
    data = r.json()
    assert data["rule_code"] == "SPD-001"
    assert data["is_active"] is True


def test_list_rules(client, admin_user, admin_auth_headers):
    client.post("/api/v1/admin/rules", headers=admin_auth_headers, json={
        "rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed"})
    r = client.get("/api/v1/admin/rules", headers=admin_auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_update_rule(client, admin_user, admin_auth_headers):
    rid = client.post("/api/v1/admin/rules", headers=admin_auth_headers, json={
        "rule_code": "SPD-001", "violation_type": "超速", "rule_type": "speed"}).json()["id"]
    r = client.patch(f"/api/v1/admin/rules/{rid}", headers=admin_auth_headers,
                     json={"is_active": False, "description": "已废弃"})
    assert r.status_code == 200
    assert r.json()["is_active"] is False
    assert r.json()["description"] == "已废弃"


def test_create_rule_requires_auth(client):
    assert client.post("/api/v1/admin/rules", json={
        "rule_code": "X", "violation_type": "A", "rule_type": "speed"}).status_code == 401


def test_delete_rule_removes_database_row(client, db, admin_user, admin_auth_headers):
    rule_id = client.post("/api/v1/admin/rules", headers=admin_auth_headers, json={
        "rule_code": "DELETE-001", "violation_type": "违停", "rule_type": "parking"
    }).json()["id"]

    response = client.delete(f"/api/v1/admin/rules/{rule_id}", headers=admin_auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert db.get(ViolationRule, rule_id) is None


def test_delete_missing_rule_returns_404(client, admin_user, admin_auth_headers):
    response = client.delete("/api/v1/admin/rules/9999", headers=admin_auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "规则不存在"}


def test_delete_rule_requires_authentication(client):
    assert client.delete("/api/v1/admin/rules/1").status_code == 401


@pytest.mark.parametrize("headers_fixture", ["auth_headers", "reviewer_auth_headers"])
def test_delete_rule_requires_admin_role(client, request, headers_fixture):
    headers = request.getfixturevalue(headers_fixture)

    assert client.delete("/api/v1/admin/rules/1", headers=headers).status_code == 403
