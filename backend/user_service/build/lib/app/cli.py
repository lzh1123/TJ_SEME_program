import argparse

from sqlalchemy.exc import OperationalError

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth import ServiceCredential
from app.services.bootstrap_service import BootstrapService


def seed_defaults() -> None:
    try:
        with SessionLocal() as db:
            BootstrapService(db).seed_defaults()
    except OperationalError as exc:
        raise SystemExit(
            "Failed to seed default data. Check that the PostgreSQL database exists and "
            "that migrations have been applied before running `python -m app.cli seed`."
        ) from exc


def create_service_credential(service_name: str, token: str) -> None:
    try:
        with SessionLocal() as db:
            existing = (
                db.query(ServiceCredential)
                .filter(ServiceCredential.service_name == service_name)
                .first()
            )
            token_hash = hash_password(token)
            if existing:
                existing.token_hash = token_hash
                existing.active = True
            else:
                db.add(ServiceCredential(service_name=service_name, token_hash=token_hash, active=True))
            db.commit()
    except OperationalError as exc:
        raise SystemExit(
            "Failed to create service credential. Check the database connection and schema first."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(prog="auth-backend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Seed default roles, permissions and policies")
    seed_parser.add_argument("--service-name", help="Optional service name to register")
    seed_parser.add_argument("--service-token", help="Optional service token to register")

    args = parser.parse_args()

    if args.command == "seed":
        seed_defaults()
        if args.service_name and args.service_token:
            create_service_credential(args.service_name, args.service_token)


if __name__ == "__main__":
    main()
