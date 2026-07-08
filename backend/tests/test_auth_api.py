"""auth 路由测试：login / me / permissions menus。"""


def test_login_success(client, make_user):
    u = make_user(role="citizen")
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "123456"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["data"]["access_token"]
    assert body["data"]["user"]["username"] == u.username


def test_login_wrong_password(client, make_user):
    u = make_user(role="citizen")
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


def test_login_unknown_user(client):
    resp = client.post("/api/v1/auth/login",
                       json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_login_disabled_account(client, make_user):
    u = make_user(role="citizen", status=0)
    resp = client.post("/api/v1/auth/login",
                       json={"username": u.username, "password": "123456"})
    assert resp.status_code == 403


def test_me_without_token_returns_403(client):
    # HTTPBearer 默认 auto_error=True → 403
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403


def test_me_with_invalid_token_returns_401(client):
    resp = client.get("/api/v1/auth/me",
                      headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_me_with_token(client, make_user, auth_header):
    u = make_user(role="reviewer")
    resp = client.get("/api/v1/auth/me", headers=auth_header("reviewer", u.id))
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == u.username


def test_menus_admin_has_system_management(client, auth_header):
    resp = client.get("/api/v1/auth/permissions/menus",
                      headers=auth_header("admin", 1))
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]["menus"]]
    assert "系统管理" in names


def test_menus_citizen_no_system_management(client, auth_header):
    resp = client.get("/api/v1/auth/permissions/menus",
                      headers=auth_header("citizen", 1))
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()["data"]["menus"]]
    assert "系统管理" not in names
