"""audit log actor_user_id column

Revision ID: 0008_audit_actor_user
Revises: 0007_callback_lifecycle
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_audit_actor_user"
down_revision = "0007_callback_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("actor_user_id", sa.Integer))
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_column("audit_logs", "actor_user_id")
