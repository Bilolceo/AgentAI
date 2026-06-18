"""callback task lifecycle fields

Revision ID: 0007_callback_lifecycle
Revises: 0006_auth_hardening
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_callback_lifecycle"
down_revision = "0006_auth_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("callback_tasks", sa.Column("assigned_to_user_id", sa.Integer, sa.ForeignKey("admin_users.id")))
    op.add_column("callback_tasks", sa.Column("resolution_notes", sa.Text))
    op.add_column("callback_tasks", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.add_column("callback_tasks", sa.Column("cancelled_at", sa.DateTime(timezone=True)))
    op.add_column("callback_tasks", sa.Column("rescheduled_at", sa.DateTime(timezone=True)))
    op.add_column("callback_tasks", sa.Column("last_status_changed_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    for col in (
        "last_status_changed_at", "rescheduled_at", "cancelled_at",
        "completed_at", "resolution_notes", "assigned_to_user_id",
    ):
        op.drop_column("callback_tasks", col)
