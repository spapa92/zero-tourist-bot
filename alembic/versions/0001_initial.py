"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-08-26

"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lead",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_inbound_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_lead_phone", "lead", ["phone"], unique=True)

    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_message_lead_id", "message", ["lead_id"])

    op.create_table(
        "outcome",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("lead.id"), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("slots", sa.JSON(), nullable=True),
        sa.Column("appointment_status", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_outcome_lead_id", "outcome", ["lead_id"])


def downgrade() -> None:
    op.drop_index("ix_outcome_lead_id", table_name="outcome")
    op.drop_table("outcome")
    op.drop_index("ix_message_lead_id", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_lead_phone", table_name="lead")
    op.drop_table("lead")
