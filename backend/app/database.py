from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def apply_schema_upgrades() -> None:
    """Apply lightweight, in-place schema upgrades for existing deployments.

    The app historically relied on ``Base.metadata.create_all`` without
    migrations, which does not add columns to already-created tables. When new
    optional columns are introduced (e.g., ``product_options.localized_name``),
    this helper performs targeted ``ALTER TABLE`` statements so existing SQLite
    databases remain usable without manual intervention.
    """

    # ``create_all`` should have already created missing tables; here we only
    # patch previously-created tables that are missing new columns.
    with engine.begin() as connection:
        inspector = inspect(connection)

        try:
            product_option_columns = {
                column["name"] for column in inspector.get_columns("product_options")
            }
        except Exception:
            # If the table does not exist yet, ``create_all`` will create it.
            product_option_columns = set()

        if "localized_name" not in product_option_columns:
            connection.execute(
                text(
                    "ALTER TABLE product_options ADD COLUMN localized_name VARCHAR(255)"
                )
            )


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
