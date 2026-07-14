"""Add system announcements.

Revision ID: a6c4e2f8b901
Revises: b4f2c8d6a109
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6c4e2f8b901"
down_revision: Union[str, Sequence[str], None] = "b4f2c8d6a109"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_announcements_created_by_users",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_announcements_updated_at",
        "announcements",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_announcements_updated_at", table_name="announcements")
    op.drop_table("announcements")
