"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-16
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.core.config import settings

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("phone_number", sa.String(32), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("preferred_language", sa.String(8)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_phone_number", "customers", ["phone_number"])

    op.create_table(
        "calls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("twilio_call_sid", sa.String(64), nullable=False, unique=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id")),
        sa.Column("from_number", sa.String(32), nullable=False),
        sa.Column("to_number", sa.String(32), nullable=False),
        sa.Column("language", sa.String(8)),
        sa.Column("status", sa.String(32), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_calls_twilio_call_sid", "calls", ["twilio_call_sid"])

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("call_id", sa.Integer, sa.ForeignKey("calls.id"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_transcripts_call_id", "transcripts", ["call_id"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("call_id", sa.Integer, sa.ForeignKey("calls.id")),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id")),
        sa.Column("service", sa.String(255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(255)),
        sa.Column("language", sa.String(8)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(settings.embedding_dim), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("call_id", sa.Integer),
        sa.Column("actor", sa.String(64), nullable=False, server_default="system"),
        sa.Column("data", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_event", "audit_logs", ["event"])
    op.create_index("ix_audit_logs_call_id", "audit_logs", ["call_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("knowledge_chunks")
    op.drop_table("bookings")
    op.drop_table("transcripts")
    op.drop_table("calls")
    op.drop_table("customers")
