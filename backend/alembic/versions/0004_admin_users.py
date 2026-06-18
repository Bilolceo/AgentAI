"""admin users (auth + rbac)

Revision ID: 0004_admin_users
Revises: 0003_knowledge_items
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_admin_users"
down_revision = "0003_knowledge_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("two_factor_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("two_factor_secret", sa.String(64)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_table("admin_users")
