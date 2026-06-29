"""create_outlines_table

Revision ID: 78ac0f50c99a
Revises: e339f3b40a0e
Create Date: 2026-06-28 22:16:29.695988
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "78ac0f50c99a"
down_revision: Union[str, Sequence[str], None] = "e339f3b40a0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outlines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("dsl", sa.Text(), nullable=False),
        sa.Column("slide_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outlines_user_id"), "outlines", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outlines_user_id"), table_name="outlines")
    op.drop_table("outlines")
