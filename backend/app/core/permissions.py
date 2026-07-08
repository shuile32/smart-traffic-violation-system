"""RBAC 权限 — 静态角色→菜单映射 + 角色依赖校验

上游方案：第一阶段不做细粒度权限表，用静态角色→菜单映射。
"""

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


class RoleChecker:
    """校验当前用户角色是否在允许列表中"""

    def __init__(self, *allowed_roles: str):
        self.allowed = set(allowed_roles)

    async def __call__(self, payload: dict = Depends(get_current_user)) -> bool:
        role = payload.get("role", "")
        if role not in self.allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return True


# ── 常用角色检查器 ──────────────────────────────

RequireAdmin = RoleChecker("admin")
RequireReviewer = RoleChecker("admin", "reviewer")
RequireCitizen = RoleChecker("citizen", "reviewer", "admin")  # 任何登录用户
RequireCamera = RoleChecker("admin", "camera")  # admin 或摄像头角色


# ── 静态菜单树 ──────────────────────────────────

MENU_TREE = [
    {
        "name": "首页", "path": "/home", "icon": "HomeFilled",
        "roles": ["citizen", "reviewer", "admin"],
    },
    {
        "name": "随手拍", "path": "/citizen", "icon": "Camera",
        "roles": ["citizen"],
        "children": [
            {"name": "违章举报", "path": "/citizen/report", "roles": ["citizen"]},
            {"name": "举报进度", "path": "/citizen/progress", "roles": ["citizen"]},
        ],
    },
    {
        "name": "审核工作台", "path": "/audit", "icon": "Monitor",
        "roles": ["reviewer", "admin"],
        "children": [
            {"name": "案件卡片流", "path": "/audit/cases", "roles": ["reviewer", "admin"]},
            {"name": "AI 问答", "path": "/audit/ai-chat", "roles": ["reviewer", "admin"]},
        ],
    },
    {
        "name": "统计分析台", "path": "/dashboard", "icon": "DataAnalysis",
        "roles": ["reviewer", "admin"],
        "children": [
            {"name": "数据概览", "path": "/dashboard/overview", "roles": ["reviewer", "admin"]},
        ],
    },
    {
        "name": "系统管理", "path": "/admin", "icon": "Setting",
        "roles": ["admin"],
        "children": [
            {"name": "用户管理", "path": "/admin/users", "roles": ["admin"]},
            {"name": "摄像头管理", "path": "/admin/cameras", "roles": ["admin"]},
        ],
    },
]


def get_menus_for_role(role_name: str) -> list[dict]:
    def filter_node(node: dict) -> dict | None:
        if role_name not in node.get("roles", []):
            return None
        children = [c for c in (filter_node(c) for c in node.get("children", [])) if c]
        node["children"] = children
        return node

    return [m for m in (filter_node(item) for item in MENU_TREE) if m]
