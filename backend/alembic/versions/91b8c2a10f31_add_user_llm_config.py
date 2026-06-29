"""add_user_llm_config

Revision ID: 91b8c2a10f31
Revises: 78ac0f50c99a
Create Date: 2026-06-29 23:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91b8c2a10f31"
down_revision: Union[str, Sequence[str], None] = "78ac0f50c99a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("llm_provider", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("llm_model", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("llm_api_base", sa.String(length=500), nullable=True))
    op.add_column("users", sa.Column("llm_api_key", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "llm_api_key")
    op.drop_column("users", "llm_api_base")
    op.drop_column("users", "llm_model")
    op.drop_column("users", "llm_provider")
