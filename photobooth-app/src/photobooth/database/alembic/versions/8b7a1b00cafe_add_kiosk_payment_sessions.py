"""add kiosk payment sessions

Revision ID: 8b7a1b00cafe
Revises: 543b0c11a790
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8b7a1b00cafe"
down_revision: str | None = "543b0c11a790"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kiosk_payment_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("inserted_bills", sa.JSON(), nullable=False),
        sa.Column("credited_amount", sa.Integer(), nullable=False),
        sa.Column("overpayment", sa.Integer(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_ids", sa.JSON(), nullable=False),
        sa.Column("printable_result_id", sa.String(), nullable=True),
        sa.Column("retakes_used", sa.Integer(), nullable=False),
        sa.Column("prints_used", sa.Integer(), nullable=False),
        sa.Column("reserved_retake", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("kiosk_payment_sessions")
