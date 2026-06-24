"""notification logs (outbound SMS audit trail)

Revision ID: 0013_notification_logs
Revises: 0012_doctors_appointments
Create Date: 2026-06-24
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_notification_logs"
down_revision = "0012_doctors_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "appointment_id",
            sa.Integer,
            sa.ForeignKey("appointments.id", ondelete="SET NULL"),
        ),
        sa.Column("to_phone", sa.String(32), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="mock"),
        sa.Column("provider_ref", sa.String(128)),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notification_logs_appointment_id", "notification_logs", ["appointment_id"])


def downgrade() -> None:
    op.drop_index("ix_notification_logs_appointment_id", table_name="notification_logs")
    op.drop_table("notification_logs")
