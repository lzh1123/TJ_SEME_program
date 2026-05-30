"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

from app.core.config import get_settings


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

settings = get_settings()

user_table = settings.user_table
verify_code_table = settings.verify_code_table
refresh_token_table = settings.refresh_token_table
role_table = settings.role_table
permission_table = settings.permission_table
user_role_table = settings.user_role_table
role_permission_table = settings.role_permission_table
service_credential_table = settings.service_credential_table
policy_rule_table = settings.policy_rule_table


def upgrade() -> None:
    op.create_table(
        user_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(f"ix_{user_table}_username", user_table, ["username"], unique=True)
    op.create_index(f"ix_{user_table}_email", user_table, ["email"], unique=True)

    op.create_table(
        verify_code_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_value", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        refresh_token_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey(f"{user_table}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(f"ix_{refresh_token_table}_token_jti", refresh_token_table, ["token_jti"], unique=True)
    op.create_index(f"ix_{refresh_token_table}_session_id", refresh_token_table, ["session_id"], unique=False)

    op.create_table(
        role_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(f"ix_{role_table}_name", role_table, ["name"], unique=True)

    op.create_table(
        permission_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(f"ix_{permission_table}_code", permission_table, ["code"], unique=True)

    op.create_table(
        user_role_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey(f"{user_table}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey(f"{role_table}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        role_permission_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey(f"{role_table}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey(f"{permission_table}.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        service_credential_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("service_name", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        f"ix_{service_credential_table}_service_name",
        service_credential_table,
        ["service_name"],
        unique=True,
    )

    op.create_table(
        policy_rule_table,
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("effect", sa.String(length=16), nullable=False),
        sa.Column("subject_kind", sa.String(length=32), nullable=False),
        sa.Column("subject_values", sa.JSON(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=128), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(f"ix_{policy_rule_table}_name", policy_rule_table, ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(f"ix_{policy_rule_table}_name", table_name=policy_rule_table)
    op.drop_table(policy_rule_table)
    op.drop_index(f"ix_{service_credential_table}_service_name", table_name=service_credential_table)
    op.drop_table(service_credential_table)
    op.drop_table(role_permission_table)
    op.drop_table(user_role_table)
    op.drop_index(f"ix_{permission_table}_code", table_name=permission_table)
    op.drop_table(permission_table)
    op.drop_index(f"ix_{role_table}_name", table_name=role_table)
    op.drop_table(role_table)
    op.drop_index(f"ix_{refresh_token_table}_session_id", table_name=refresh_token_table)
    op.drop_index(f"ix_{refresh_token_table}_token_jti", table_name=refresh_token_table)
    op.drop_table(refresh_token_table)
    op.drop_table(verify_code_table)
    op.drop_index(f"ix_{user_table}_email", table_name=user_table)
    op.drop_index(f"ix_{user_table}_username", table_name=user_table)
    op.drop_table(user_table)
