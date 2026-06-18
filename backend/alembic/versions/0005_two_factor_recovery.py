"""2fa recovery codes column

Revision ID: 0005_two_factor_recovery
Revises: 0004_admin_users
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_two_factor_recovery"
down_revision = "0004_admin_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admin_users", sa.Column("two_factor_recovery_codes", sa.JSON))


def downgrade() -> None:
    op.drop_column("admin_users", "two_factor_recovery_codes")
