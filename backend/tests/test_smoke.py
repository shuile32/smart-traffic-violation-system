"""验证 conftest 基础设施可用。"""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_db_session_writable(db_session):
    from app.models.role import Role

    db_session.add(Role(name="smoke_role"))
    db_session.commit()
    assert db_session.query(Role).filter_by(name="smoke_role").count() == 1


def test_celery_fake_records(celery_calls):
    # conftest 已注入 fake；直接调用确认记录链路
    from app.tasks.detect_objects_task import detect_objects_task

    detect_objects_task.delay(1, "/x.jpg")
    assert any(c[0] == "delay" for c in celery_calls)
