"""callback tasks (operator transfer engine)

Revision ID: 0002_callback_tasks
Revises: 0001_initial
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_callback_tasks"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "callback_tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("call_session_id", sa.Integer, sa.ForeignKey("calls.id"), nullable=False),
        sa.Column("patient_phone", sa.String(32)),
        sa.Column("reason", sa.String(48), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="callback_required"),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_callback_tasks_call_session_id", "callback_tasks", ["call_session_id"])


def downgrade() -> None:
    op.drop_table("callback_tasks")
