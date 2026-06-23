"""doctors + appointments (manager schedule, M2)

Revision ID: 0012_doctors_appointments
Revises: 0011_telephony_streams
Create Date: 2026-06-23
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_doctors_appointments"
down_revision = "0011_telephony_streams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("specialty", sa.String(64)),
        sa.Column("room", sa.String(64)),
        sa.Column("working_days", sa.String(64)),
        sa.Column("working_hours", sa.String(64)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("doctor_id", sa.Integer, sa.ForeignKey("doctors.id")),
        sa.Column("call_session_id", sa.Integer, sa.ForeignKey("calls.id")),
        sa.Column("patient_name", sa.String(255)),
        sa.Column("patient_phone", sa.String(32)),
        sa.Column("service", sa.String(255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("duration_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(16), nullable=False, server_default="manual"),
        sa.Column("operator_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"])


def downgrade() -> None:
    op.drop_index("ix_appointments_scheduled_at", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("doctors")
