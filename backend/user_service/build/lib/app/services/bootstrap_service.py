from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import Permission, PolicyRule, Role, RolePermission


class BootstrapService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_create_role(self, name: str, description: str | None = None) -> Role:
        role = self.db.execute(select(Role).where(Role.name == name)).scalars().first()
        if role:
            return role
        role = Role(name=name, description=description)
        self.db.add(role)
        self.db.flush()
        return role

    def _get_or_create_permission(self, code: str, description: str | None = None) -> Permission:
        permission = self.db.execute(select(Permission).where(Permission.code == code)).scalars().first()
        if permission:
            return permission
        permission = Permission(code=code, description=description)
        self.db.add(permission)
        self.db.flush()
        return permission

    def _ensure_role_permission(self, role_id: int, permission_id: int) -> None:
        existing = self.db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        ).scalars().first()
        if existing:
            return
        self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))

    def _ensure_policy_rule(
        self,
        *,
        name: str,
        effect: str,
        subject_kind: str,
        subject_values: list[str],
        action: str,
        resource_type: str,
        conditions: dict,
        description: str | None = None,
    ) -> None:
        existing = self.db.execute(select(PolicyRule).where(PolicyRule.name == name)).scalars().first()
        if existing:
            return
        self.db.add(
            PolicyRule(
                name=name,
                effect=effect,
                subject_kind=subject_kind,
                subject_values=subject_values,
                action=action,
                resource_type=resource_type,
                conditions=conditions,
                description=description,
                active=True,
            )
        )

    def seed_defaults(self) -> None:
        user_role = self._get_or_create_role("user", "Default end-user role")
        admin_role = self._get_or_create_role("admin", "Administrator role")

        permissions = {
            "user_profile:read": "Read user profile",
            "user_profile:update": "Update user profile",
            "report:read": "Read report resources",
            "report:update": "Update report resources",
            "auth:manage": "Manage authentication lifecycle",
        }
        created_permissions = {
            code: self._get_or_create_permission(code, description)
            for code, description in permissions.items()
        }

        for code, permission in created_permissions.items():
            self._ensure_role_permission(admin_role.id, permission.id)
            if code in {"user_profile:read", "user_profile:update"}:
                self._ensure_role_permission(user_role.id, permission.id)

        self._ensure_policy_rule(
            name="allow-internal-report-read",
            effect="allow",
            subject_kind="any",
            subject_values=[],
            action="read",
            resource_type="report",
            conditions={"is_internal": True},
            description="Allow internal callers to read report resources",
        )

        self._ensure_policy_rule(
            name="allow-self-user-profile",
            effect="allow",
            subject_kind="any",
            subject_values=[],
            action="*",
            resource_type="user_profile",
            conditions={"self_access": True},
            description="Fallback self-access policy for user profile resources",
        )

        self.db.commit()

