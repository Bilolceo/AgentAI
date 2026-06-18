"""telephony media streams (websocket spike)

Revision ID: 0011_telephony_streams
Revises: 0010_telephony_calls
Create Date: 2026-06-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_telephony_streams"
down_revision = "0010_telephony_calls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "telephony_streams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(24), nullable=False, server_default="twilio"),
        sa.Column("provider_call_id", sa.String(128)),
        sa.Column("stream_sid", sa.String(128)),
        sa.Column("telephony_call_id", sa.Integer, sa.ForeignKey("telephony_calls.id")),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("media_frames_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("media_bytes_count", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("last_sequence_number", sa.Integer),
        sa.Column("stream_metadata", sa.JSON),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("stopped_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_telephony_streams_provider", "telephony_streams", ["provider"])
    op.create_index(
        "ix_telephony_streams_provider_call_id", "telephony_streams", ["provider_call_id"]
    )
    op.create_index("ix_telephony_streams_stream_sid", "telephony_streams", ["stream_sid"])
    op.create_index(
        "ix_telephony_streams_telephony_call_id", "telephony_streams", ["telephony_call_id"]
    )


def downgrade() -> None:
    op.drop_table("telephony_streams")
