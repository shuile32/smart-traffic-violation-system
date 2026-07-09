def test_list_audit_logs(client, admin_user, admin_auth_headers):
    r = client.get("/api/v1/admin/audit-logs", headers=admin_auth_headers)
    assert r.status_code == 200
    assert "items" in r.json()


def test_list_audit_logs_requires_auth(client):
    assert client.get("/api/v1/admin/audit-logs").status_code == 401
