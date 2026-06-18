"""telephony calls (intake spike)

Revision ID: 0010_telephony_calls
Revises: 0009_audio_recordings
Create Date: 2026-06-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_telephony_calls"
down_revision = "0009_audio_recordings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telephony_calls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("provider_call_id", sa.String(128)),
        sa.Column("call_session_id", sa.Integer, sa.ForeignKey("calls.id")),
        sa.Column("from_number", sa.String(32)),
        sa.Column("to_number", sa.String(32)),
        sa.Column("status", sa.String(24), nullable=False, server_default="received"),
        sa.Column("direction", sa.String(16), nullable=False, server_default="inbound"),
        sa.Column("raw_metadata", sa.JSON),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_telephony_calls_provider", "telephony_calls", ["provider"])
    op.create_index(
        "ix_telephony_calls_provider_call_id", "telephony_calls", ["provider_call_id"]
    )
    op.create_index(
        "ix_telephony_calls_call_session_id", "telephony_calls", ["call_session_id"]
    )


def downgrade() -> None:
    op.drop_table("telephony_calls")
