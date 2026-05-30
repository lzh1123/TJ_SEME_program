from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIMessage(BaseModel):
    message: str


class UserSubject(BaseModel):
    id: int
    username: str
    email: str
    status: str
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class IntrospectResponse(BaseModel):
    active: bool
    subject: UserSubject | None = None
    token_type: str | None = None
    expires_at: int | None = None


class AuthorizeDecision(BaseModel):
    allowed: bool
    reason: str
    matched_permissions: list[str] = []


class ABACResource(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    id: str | int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ABACContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    attributes: dict[str, Any] = Field(default_factory=dict)
