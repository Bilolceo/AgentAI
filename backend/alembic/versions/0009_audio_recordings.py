"""audio recordings (voice layer metadata)

Revision ID: 0009_audio_recordings
Revises: 0008_audit_actor_user
Create Date: 2026-06-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_audio_recordings"
down_revision = "0008_audit_actor_user"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audio_recordings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("call_session_id", sa.Integer, sa.ForeignKey("calls.id"), nullable=False),
        sa.Column("call_message_id", sa.Integer, sa.ForeignKey("transcripts.id")),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("storage_provider", sa.String(24), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("transcript_text", sa.Text),
        sa.Column("transcript_language", sa.String(16)),
        sa.Column("transcript_confidence", sa.Float),
        sa.Column("tts_voice", sa.String(64)),
        sa.Column("tts_text", sa.Text),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_audio_recordings_call_session_id", "audio_recordings", ["call_session_id"]
    )


def downgrade() -> None:
    op.drop_table("audio_recordings")
