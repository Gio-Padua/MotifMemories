"""Kiosk review, filter source and durable customer delivery."""

import sqlalchemy as sa
from alembic import op

revision = "91f17e42ab01"
down_revision = "8b7a1b00cafe"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("kiosk_payment_sessions", sa.Column("presentation_stage", sa.String(), nullable=False, server_default="delivery"))
    op.add_column("kiosk_payment_sessions", sa.Column("selected_filter", sa.String(), nullable=False, server_default="original"))
    op.add_column("mediaitems", sa.Column("filter_source", sa.String(), nullable=True))
    op.add_column("mediaitems", sa.Column("customer_delivery", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("mediaitems") as batch:
        batch.drop_column("customer_delivery")
        batch.drop_column("filter_source")
    with op.batch_alter_table("kiosk_payment_sessions") as batch:
        batch.drop_column("selected_filter")
        batch.drop_column("presentation_stage")
