"""TDD: JWT token + 密码哈希"""

import sys
sys.path.insert(0, ".")

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.permissions import get_menus_for_role, RoleChecker


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "admin123"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token(user_id=1, role="admin")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["role"] == "admin"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.token") is None
        assert decode_access_token("") is None


class TestMenus:
    def test_admin_sees_all(self):
        menus = get_menus_for_role("admin")
        names = [m["name"] for m in menus]
        assert "系统管理" in names
        assert "审核工作台" in names

    def test_reviewer_no_admin(self):
        menus = get_menus_for_role("reviewer")
        names = [m["name"] for m in menus]
        assert "审核工作台" in names
        assert "系统管理" not in names

    def test_citizen_no_audit(self):
        menus = get_menus_for_role("citizen")
        names = [m["name"] for m in menus]
        assert "随手拍" in names
        assert "审核工作台" not in names
