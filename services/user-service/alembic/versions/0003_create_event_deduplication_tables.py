"""create event deduplication tables

Revision ID: 0003_create_event_deduplication_tables
Revises: 0002_add_xp_and_level_to_users
Create Date: 2026-04-21 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_create_event_deduplication_tables"
down_revision = "0002_add_xp_and_level_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("xp_awarded", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("result_xp", sa.Integer(), nullable=True),
        sa.Column("result_level", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.Text(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_processed_events_status",
        ),
        sa.UniqueConstraint("answer_id", name="uq_processed_events_answer_id"),
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("response_xp", sa.Integer(), nullable=True),
        sa.Column("response_level", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.Text(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_idempotency_keys_status",
        ),
        sa.UniqueConstraint("key", name="uq_idempotency_keys_key"),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("processed_events")
