"""screenshot and video columns

Revision ID: 18141fc701fd
Revises: e4f6d47be7f3
Create Date: 2026-02-07 00:26:48.754832

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18141fc701fd"
down_revision: str | Sequence[str] | None = "e4f6d47be7f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("test_runs", sa.Column("video_name", sa.String(length=255), nullable=True))
    op.add_column("test_runs", sa.Column("screenshot_name", sa.String(length=255), nullable=True))

    # optional indexes
    op.create_index("ix_test_runs_video_name", "test_runs", ["video_name"])
    op.create_index("ix_test_runs_screenshot_name", "test_runs", ["screenshot_name"])


def downgrade() -> None:
    op.drop_index("ix_test_runs_screenshot_name", table_name="test_runs")
    op.drop_index("ix_test_runs_video_name", table_name="test_runs")

    op.drop_column("test_runs", "screenshot_name")
    op.drop_column("test_runs", "video_name")
