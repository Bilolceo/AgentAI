"""structured knowledge base items

Revision ID: 0003_knowledge_items
Revises: 0002_callback_tasks
Create Date: 2026-06-17
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_knowledge_items"
down_revision = "0002_callback_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_uz", sa.Text, nullable=False),
        sa.Column("content_ru", sa.Text, nullable=False),
        sa.Column("tags", sa.JSON),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_items_category", "knowledge_items", ["category"])
    op.create_index("ix_knowledge_items_is_active", "knowledge_items", ["is_active"])


def downgrade() -> None:
    op.drop_table("knowledge_items")
