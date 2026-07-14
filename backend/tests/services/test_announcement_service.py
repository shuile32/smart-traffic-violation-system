from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.announcement import Announcement
from app.models.violation import AuditLog
from app.schemas.announcement import (
    AnnouncementCreateIn,
    AnnouncementListResponse,
    AnnouncementOut,
    AnnouncementUpdateIn,
)
from app.services.announcement_service import AnnouncementService


def test_announcement_model_declares_updated_at_index():
    assert {index.name for index in Announcement.__table__.indexes} == {
        "ix_announcements_updated_at"
    }


def test_create_trims_values_and_writes_audit_log(db, admin_user):
    created = AnnouncementService(db).create(
        title="  道路施工提醒  ",
        content="  人民路临时封闭。  ",
        actor_id=admin_user.id,
    )

    assert (created.title, created.content) == ("道路施工提醒", "人民路临时封闭。")
    assert created.created_by == admin_user.id
    log = (
        db.query(AuditLog)
        .filter_by(target_type="announcement", target_id=created.id)
        .one()
    )
    assert log.action == "announcement_create"
    assert log.actor_id == admin_user.id
    assert created.title in log.detail
    assert len(log.detail) <= 512


def test_list_announcements_uses_stable_updated_at_and_id_order(db, admin_user):
    service = AnnouncementService(db)
    first = service.create(title="第一条", content="正文", actor_id=admin_user.id)
    second = service.create(title="第二条", content="正文", actor_id=admin_user.id)
    third = service.create(title="第三条", content="正文", actor_id=admin_user.id)
    older = datetime(2026, 1, 1, tzinfo=timezone.utc)
    newer = datetime(2026, 1, 2, tzinfo=timezone.utc)
    first.updated_at = older
    second.updated_at = newer
    third.updated_at = newer
    db.commit()

    result = service.list_announcements(page=1, page_size=2)

    assert result == {
        "items": [third, second],
        "total": 3,
        "page": 1,
        "page_size": 2,
    }


def test_update_is_partial_and_writes_audit_log(db, admin_user):
    service = AnnouncementService(db)
    created = service.create(
        title="道路施工提醒", content="人民路临时封闭。", actor_id=admin_user.id
    )

    updated = service.update(
        created.id,
        title="  调整后的提醒  ",
        content=None,
        actor_id=admin_user.id,
    )

    assert updated.title == "调整后的提醒"
    assert updated.content == "人民路临时封闭。"
    logs = (
        db.query(AuditLog)
        .filter_by(target_type="announcement", target_id=created.id)
        .order_by(AuditLog.id)
        .all()
    )
    assert [log.action for log in logs] == [
        "announcement_create",
        "announcement_update",
    ]
    assert updated.title in logs[-1].detail


def test_delete_removes_announcement_and_keeps_audit_log(db, admin_user):
    service = AnnouncementService(db)
    created = service.create(title="临时公告", content="正文", actor_id=admin_user.id)

    service.delete(created.id, actor_id=admin_user.id)

    assert db.get(Announcement, created.id) is None
    log = (
        db.query(AuditLog)
        .filter_by(
            action="announcement_delete",
            target_type="announcement",
            target_id=created.id,
        )
        .one()
    )
    assert created.title in log.detail


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_announcement_raises_404(db, admin_user, operation):
    service = AnnouncementService(db)

    with pytest.raises(HTTPException) as exc_info:
        if operation == "get":
            service.get(9999)
        elif operation == "update":
            service.update(
                9999, title="不存在", content=None, actor_id=admin_user.id
            )
        else:
            service.delete(9999, actor_id=admin_user.id)

    assert exc_info.value.status_code == 404


def test_announcement_schemas_trim_and_serialize(db, admin_user):
    create_input = AnnouncementCreateIn(title="  标题  ", content="  正文  ")
    update_input = AnnouncementUpdateIn(title="  新标题  ")
    created = AnnouncementService(db).create(
        title=create_input.title,
        content=create_input.content,
        actor_id=admin_user.id,
    )

    assert create_input.model_dump() == {"title": "标题", "content": "正文"}
    assert update_input.model_dump() == {"title": "新标题", "content": None}
    output = AnnouncementOut.model_validate(created)
    response = AnnouncementListResponse(
        items=[output], total=1, page=1, page_size=20
    )
    assert response.items[0].id == created.id


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (AnnouncementCreateIn, {"title": "   ", "content": "正文"}),
        (AnnouncementCreateIn, {"title": "标题", "content": "   "}),
        (AnnouncementCreateIn, {"title": "题" * 101, "content": "正文"}),
        (AnnouncementCreateIn, {"title": "标题", "content": "文" * 5001}),
        (AnnouncementUpdateIn, {}),
        (AnnouncementUpdateIn, {"title": "   "}),
        (AnnouncementUpdateIn, {"content": "文" * 5001}),
    ],
)
def test_announcement_schemas_reject_invalid_inputs(schema, payload):
    with pytest.raises(ValidationError):
        schema.model_validate(payload)
