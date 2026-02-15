"""artifact keys colunms

Revision ID: e6a59a9f38ca
Revises: 18141fc701fd
Create Date: 2026-02-07 21:38:51.322256

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6a59a9f38ca"
down_revision: str | Sequence[str] | None = "18141fc701fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("test_runs", sa.Column("video_object_key", sa.String(length=1024), nullable=True))
    op.add_column(
        "test_runs", sa.Column("screenshot_object_key", sa.String(length=1024), nullable=True)
    )


def downgrade() -> None:
    op.drop_index("ix_test_runs_screenshot_object_key", table_name="test_runs")
    op.drop_index("ix_test_runs_video_object_key", table_name="test_runs")
