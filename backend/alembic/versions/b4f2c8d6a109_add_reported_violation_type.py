"""Add the reported violation type to intake events.

Revision ID: b4f2c8d6a109
Revises: 9a3b5c7d1e2f
Create Date: 2026-07-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4f2c8d6a109"
down_revision: Union[str, Sequence[str], None] = "9a3b5c7d1e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "intake_events",
        sa.Column("reported_violation_type", sa.String(length=32), nullable=True),
    )
    op.alter_column(
        "cases",
        "ai_result_json",
        existing_type=sa.String(length=4096),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "cases",
        "ai_result_json",
        existing_type=sa.Text(),
        type_=sa.String(length=4096),
        existing_nullable=True,
    )
    op.drop_column("intake_events", "reported_violation_type")
