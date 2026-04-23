"""fix processed events unique constraint

Revision ID: 0004_fix_unique_constraint_events
Revises: 0003_create_event_deduplication_tables
Create Date: 2026-04-21 00:00:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_fix_unique_constraint_events"
down_revision = "0003_create_event_deduplication_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("processed_events") as batch_op:
        batch_op.drop_constraint("uq_processed_events_answer_id", type_="unique")
        batch_op.create_unique_constraint(
            "uq_processed_events_user_answer",
            ["user_id", "answer_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("processed_events") as batch_op:
        batch_op.drop_constraint("uq_processed_events_user_answer", type_="unique")
        batch_op.create_unique_constraint(
            "uq_processed_events_answer_id",
            ["answer_id"],
        )
