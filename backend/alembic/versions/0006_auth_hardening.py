"""auth hardening: token_version + force_password_change

Revision ID: 0006_auth_hardening
Revises: 0005_two_factor_recovery
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_auth_hardening"
down_revision = "0005_two_factor_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admin_users",
        sa.Column("token_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.add_column(
        "admin_users",
        sa.Column("force_password_change", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("admin_users", "force_password_change")
    op.drop_column("admin_users", "token_version")
