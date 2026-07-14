"""Merge email verification and system announcements migration heads."""

from typing import Sequence, Union


revision: str = "20260714_130000"
down_revision: Union[str, Sequence[str], None] = (
    "20260714_120000",
    "a6c4e2f8b901",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
