"""种子数据：角色、管理员账号、违章规则、通知模板"""

import json
import sys
sys.path.insert(0, ".")

from app.core.database import engine, SessionLocal, Base
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.violation_rule import ViolationRule
from app.models.notification_template import NotificationTemplate


def seed():
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表已创建")

    db = SessionLocal()
    try:
        # 1. 角色：citizen / reviewer / admin / camera
        roles_data = [
            ("admin", "超级管理员/运维人员"),
            ("reviewer", "审核管理员"),
            ("citizen", "普通市民"),
            ("camera", "摄像头设备"),
        ]
        roles = {}
        for name, desc in roles_data:
            role = db.query(Role).filter(Role.name == name).first()
            if not role:
                role = Role(name=name, description=desc)
                db.add(role)
                db.flush()
            roles[name] = role
        db.commit()
        print("✅ 角色: admin, reviewer, citizen, camera")

        # 2. 默认管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                phone="13800000000",
                email="admin@traffic.local",
                role_id=roles["admin"].id,
                status=1,
            )
            db.add(admin)
        db.commit()
        print("✅ 管理员: admin / admin123")

        # 3. 默认审核员
        reviewer = db.query(User).filter(User.username == "reviewer").first()
        if not reviewer:
            reviewer = User(
                username="reviewer",
                password_hash=hash_password("reviewer123"),
                phone="13800000001",
                email="reviewer@traffic.local",
                role_id=roles["reviewer"].id,
                status=1,
            )
            db.add(reviewer)
        db.commit()
        print("✅ 审核员: reviewer / reviewer123")

        # 4. 违章规则 — 超速 + 占用专用车道
        rules_data = [
            (
                "SPD-001", "超速", "speed",
                json.dumps({"speed_limit": 60, "road_segment": "默认路段"}),
                "超速行驶：车速超过路段限速即构成违章",
            ),
            (
                "LANE-001", "占用专用车道", "special_lane",
                json.dumps({
                    "lane_roi": [[100, 200], [500, 200], [500, 400], [100, 400]],
                    "allowed_vehicle_types": ["bus"],
                    "time_window": {"start": "07:00", "end": "09:00"},
                }),
                "占用公交专用车道：非公交车在限行时段（7:00-9:00）位于专用车道 ROI 内",
            ),
        ]
        for code, vtype, rtype, params, desc in rules_data:
            existing = db.query(ViolationRule).filter(ViolationRule.rule_code == code).first()
            if not existing:
                rule = ViolationRule(
                    rule_code=code,
                    violation_type=vtype,
                    rule_type=rtype,
                    params=params,
                    description=desc,
                    is_active=True,
                )
                db.add(rule)
        db.commit()
        print("✅ 违章规则: 超速(SPD-001) + 占用专用车道(LANE-001)")

        # 5. 通知模板
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.template_code == "violation_notify"
        ).first()
        if not template:
            template = NotificationTemplate(
                template_code="violation_notify",
                template_name="违章通知邮件",
                channel="email",
                subject="您的车辆 {{ plate_no }} 有一条新的交通违章记录",
                body_html="""<h3>交通违章通知</h3>
<table>
<tr><td>车牌号：</td><td>{{ plate_no }}</td></tr>
<tr><td>违章类型：</td><td>{{ violation_type }}</td></tr>
<tr><td>违章时间：</td><td>{{ occurred_at }}</td></tr>
<tr><td>违章地点：</td><td>{{ location_text }}</td></tr>
<tr><td>罚款金额：</td><td>{{ fine_amount }} 元</td></tr>
<tr><td>扣分：</td><td>{{ points }} 分</td></tr>
</table>
<p>如有疑问，请登录系统查看详情。</p>""",
                variables='["plate_no","violation_type","occurred_at","location_text","fine_amount","points"]',
            )
            db.add(template)
        db.commit()
        print("✅ 通知模板: violation_notify")

    finally:
        db.close()

    print("\n🎉 种子数据初始化完毕！")


if __name__ == "__main__":
    seed()
