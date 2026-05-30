# API Reference

## Public Auth APIs

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/verify-code/send`
- `POST /auth/verify-code/check`

## Internal Identity APIs

- `GET /auth/me`
- `POST /auth/introspect`
- `POST /auth/authorize`
- `GET /auth/permissions`
- `GET /auth/roles`

## Notes

- `introspect` and `authorize` require `X-Service-Name` and `X-Service-Token`, or the fallback `INTERNAL_SERVICE_TOKEN`.
- `authorize` accepts `subject + action + resource + context`.
- `resource` uses `{ "type": "...", "id": "...", "attributes": {...} }`.
- `context` uses `{ "attributes": {...} }`.
- In JWT-only mode, `logout` is not supported.
- The base auth endpoints (`/auth/register`, `/auth/login`, `/auth/reset-password`) expect password values that have already been transformed by a client-side transport hash.
- The `client-*` endpoints simulate that client-side transform on the server and forward the result to the original endpoints.

## Client Compatibility APIs

- `POST /auth/client-register`
- `POST /auth/client-login`
- `POST /auth/client-reset-password`

## Example: register

```json
{
  "email": "user@example.com",
  "username": "user1",
  "password": "client-side-hash-output",
  "verification_code": "123456"
}
```

## Example: authorize

```json
{
  "subject": {
    "id": 1,
    "username": "user1",
    "email": "user@example.com",
    "status": "active",
    "roles": ["user"],
    "permissions": ["user_profile:read"]
  },
  "action": "read",
  "resource": {
    "type": "report",
    "id": "r-1",
    "attributes": {}
  },
  "context": {
    "attributes": {
      "is_internal": true
    }
  }
}
```

## Password Transport Rule

For compatibility, password-related payloads are handled in two layers:

- Base endpoints receive the already transformed password string.
- `client-*` endpoints accept the plain password, apply the transport hash, and then call the base endpoints internally.

This keeps the original API behavior intact while providing a browser-friendly compatibility path.
