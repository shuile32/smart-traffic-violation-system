"""API 层测试基础设施。

设计要点：
1. 在 import app 之前用环境变量把 DATABASE_URL 切到 MySQL 测试库。
2. 注入 5 个 fake task 模块到 sys.modules，隔绝 ultralytics/paddleocr/Redis。
3. Session 用 join_transaction_mode="create_savepoint"，每用例事务回滚隔离。
4. monkeypatch intakes.chain 与运行期 intakes.MEDIA_DIR。
"""
import os
import sys
import types
import tempfile
import shutil

# ── 在导入 app 之前配置环境 ─────────────────────────────
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "mysql+pymysql://root:123456@localhost:3306/traffic_violation_test",  # 本地开发凭据，CI 用 env 覆盖
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("DEBUG", "false")          # 关闭 SQL echo 噪声
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "30")
_media_tmp = tempfile.mkdtemp(prefix="tv_media_")
os.environ.setdefault("MEDIA_STORAGE_DIR", _media_tmp)

# ── 注入 fake task 模块，避免拉起 ultralytics/paddleocr/Redis ──
CELERY_CALLS: list = []


class _FakeTask:
    """假 Celery task：记录调用但不执行，不连 broker。"""

    def __init__(self, name: str):
        self.name = name

    def s(self, *a, **k):
        CELERY_CALLS.append(("s", self.name, a, k))
        return {"task": self.name, "args": a, "kwargs": k}

    def si(self, *a, **k):
        # si 仅构建签名，不应有副作用，故不调用 s 也不记录。
        return {"task": self.name, "args": a, "kwargs": k}

    def delay(self, *a, **k):
        CELERY_CALLS.append(("delay", self.name, a, k))
        return None

    def apply_async(self, args=None, kwargs=None, **options):
        CELERY_CALLS.append(("apply_async", self.name, args, kwargs, options))
        return None


_FAKE_TASK_MODULES = {
    "app.tasks.detect_objects_task": ("detect_objects_task",),
    "app.tasks.ocr_plate_task": ("ocr_plate_task",),
    "app.tasks.evaluate_rule_task": ("evaluate_rule_task",),
    "app.tasks.ai_review_task": ("ai_review_task",),
    "app.tasks.send_notification_task": ("send_notification_task",),
}
for _mod_name, _names in _FAKE_TASK_MODULES.items():
    if _mod_name not in sys.modules:
        _fake = types.ModuleType(_mod_name)
        for _n in _names:
            setattr(_fake, _n, _FakeTask(_n))
        sys.modules[_mod_name] = _fake

# ── 现在才导入 app ──────────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401  注册所有模型到 Base.metadata
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app

engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)


class _FakeWorkflow:
    def apply_async(self, args=None, kwargs=None, **options):
        CELERY_CALLS.append(("chain.apply_async", args, kwargs, options))
        return None


def _fake_chain(*sigs):
    CELERY_CALLS.append(("chain", sigs))
    return _FakeWorkflow()


# 替换 intakes 模块里的 chain（其 _create_case 用 chain(...).apply_async()）
import app.api.v1.intakes as _intakes_mod  # noqa: E402
_intakes_mod.chain = _fake_chain
_intakes_mod.MEDIA_DIR = _media_tmp  # 默认指向临时目录，安全网；Task 3 仍可按用例 monkeypatch 覆盖


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(engine)
    yield
    # cases ↔ ai_review_results 存在循环外键且约束未命名，drop_all 的拓扑排序会失败；
    # 关闭 FK 检查后逐表 DROP，绕过循环依赖（仅测试 teardown，不动生产模型）。
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=0")
        for _t_name in Base.metadata.tables:
            conn.execute(text(f"DROP TABLE IF EXISTS `{_t_name}`"))
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
    shutil.rmtree(_media_tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
def _reset_celery():
    CELERY_CALLS.clear()
    yield


@pytest.fixture
def celery_calls():
    return CELERY_CALLS


@pytest.fixture
def db_session():
    connection = engine.connect()
    trans = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    yield session
    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_roles(db_session):
    from app.models.role import Role

    for name in ("citizen", "reviewer", "admin", "camera"):
        db_session.add(Role(name=name, description=name))
    db_session.commit()
    return {r.name: r.id for r in db_session.query(Role).all()}


@pytest.fixture
def make_user(db_session, seed_roles):
    from app.models.user import User

    counter = {"n": 0}

    def _make(role: str = "citizen", status: int = 1):
        counter["n"] += 1
        u = User(
            username=f"u{counter['n']}",
            password_hash=hash_password("123456"),
            role_id=seed_roles[role],
            status=status,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        return u

    return _make


@pytest.fixture
def auth_header():
    def _make(role: str = "citizen", user_id: int = 1):
        token = create_access_token(user_id, role)
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def seed_camera(db_session):
    import hashlib
    from app.models.camera_device import CameraDevice
    from app.models.camera_api_key import CameraApiKey

    dev = CameraDevice(device_name="cam1", device_code="DEV001", location_text="路口A")
    db_session.add(dev)
    db_session.commit()
    db_session.refresh(dev)
    raw_key = "test-camera-key-123"
    db_session.add(CameraApiKey(
        camera_device_id=dev.id,
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        key_prefix=raw_key[:8],
        status="active",
    ))
    db_session.commit()
    return {"device": dev, "raw_key": raw_key}
