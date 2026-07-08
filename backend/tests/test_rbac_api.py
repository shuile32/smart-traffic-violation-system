"""RBAC 测试：经真实端点验证 RoleChecker 对各角色的 200/403 决策。"""

WIN = {"start_time": "2026-01-01T00:00:00", "end_time": "2026-12-31T23:59:59"}


def test_admin_can_access_reviewer_endpoint(client, make_user, auth_header):
    u = make_user(role="admin")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("admin", u.id), params=WIN)
    assert resp.status_code == 200


def test_reviewer_can_access(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("reviewer", u.id), params=WIN)
    assert resp.status_code == 200


def test_citizen_blocked_from_reviewer_endpoint(client, make_user, auth_header):
    u = make_user(role="citizen")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("citizen", u.id), params=WIN)
    assert resp.status_code == 403


def test_camera_role_blocked(client, make_user, auth_header):
    u = make_user(role="camera")
    resp = client.get("/api/v1/statistics/overview",
                      headers=auth_header("camera", u.id), params=WIN)
    assert resp.status_code == 403


def test_admin_can_access_cases_list(client, make_user, auth_header):
    u = make_user(role="admin")
    resp = client.get("/api/v1/cases", headers=auth_header("admin", u.id))
    assert resp.status_code == 200
