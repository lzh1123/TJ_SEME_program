from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.auth import Permission, PolicyRule, Role, RolePermission, ServiceCredential, UserRole
from app.models.user import User


class AuthorizationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_roles(self, user_id: int) -> list[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_permissions(self, user_id: int) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        return sorted(set(self.db.execute(stmt).scalars().all()))

    def build_subject(self, user: User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "status": user.status,
            "roles": self.get_roles(user.id),
            "permissions": self.get_permissions(user.id),
        }

    def verify_service_credential(self, service_name: str, token: str) -> bool:
        credential = self.db.execute(
            select(ServiceCredential).where(
                ServiceCredential.service_name == service_name,
                ServiceCredential.active.is_(True),
            )
        ).scalars().first()
        if not credential:
            return False
        return verify_password(token, credential.token_hash)

    def _subject_matches(self, subject: dict, rule: PolicyRule) -> bool:
        subject_kind = rule.subject_kind
        if subject_kind in {"any", "*"}:
            return True
        if subject_kind == "user" and int(subject.get("id", -1)) in [int(v) for v in rule.subject_values]:
            return True
        if subject_kind == "role":
            subject_roles = set(subject.get("roles", []))
            return bool(subject_roles.intersection(set(rule.subject_values)))
        if subject_kind == "permission":
            subject_permissions = set(subject.get("permissions", []))
            return bool(subject_permissions.intersection(set(rule.subject_values)))
        return False

    def _context_matches(self, context: dict | None, conditions: dict) -> bool:
        if not conditions:
            return True
        if not context:
            return False
        attributes = context.get("attributes", {})
        for key, expected in conditions.items():
            if attributes.get(key) != expected:
                return False
        return True

    def authorize(
        self,
        subject: dict,
        action: str,
        resource: dict,
        context: dict | None = None,
    ) -> tuple[bool, str, list[str]]:
        permissions = subject.get("permissions", [])
        resource_type = resource.get("type", "*")
        candidates = [
            f"{resource_type}:{action}",
            f"{resource_type}:*",
            f"*:{action}",
            "*:*",
        ]
        matched = [permission for permission in permissions if permission in candidates]
        if matched:
            return True, "allowed by RBAC permission", matched

        rules = self.db.execute(
            select(PolicyRule).where(PolicyRule.active.is_(True)).order_by(PolicyRule.id.asc())
        ).scalars().all()
        for rule in rules:
            if rule.effect != "allow":
                continue
            action_match = rule.action in {"*", action}
            resource_match = rule.resource_type in {"*", resource_type}
            if not action_match or not resource_match:
                continue
            if not self._subject_matches(subject, rule):
                continue
            if rule.conditions.get("self_access") is True:
                resource_id = resource.get("id")
                if resource_id is None or str(resource_id) != str(subject.get("id")):
                    continue
            if not self._context_matches(context, rule.conditions):
                continue
            return True, f"allowed by policy rule {rule.name}", []

        resource_id = resource.get("id")
        if (
            resource_type == "user_profile"
            and action in {"read", "update"}
            and resource_id is not None
            and str(resource_id) == str(subject.get("id"))
        ):
            return True, "allowed by ABAC self-access rule", []

        if context and context.get("attributes", {}).get("is_internal") is True:
            return True, "allowed by ABAC internal context rule", []

        return False, "no matching policy", []
