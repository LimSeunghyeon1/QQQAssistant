from __future__ import annotations

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

        # Patch ``product_options`` schema
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

        # Patch ``products`` schema for newly added description and image columns
        try:
            product_columns = {
                column["name"] for column in inspector.get_columns("products")
            }
        except Exception:
            product_columns = set()

        def add_product_column(column_name: str, ddl: str) -> None:
            if column_name not in product_columns:
                connection.execute(
                    text(f"ALTER TABLE products ADD COLUMN {column_name} {ddl}")
                )

        add_product_column("raw_description", "TEXT")
        add_product_column("thumbnail_image_urls", "JSON DEFAULT '[]'")
        add_product_column("detail_image_urls", "JSON DEFAULT '[]'")
        add_product_column("exchange_rate", "NUMERIC(12, 4)")
        add_product_column("margin_rate", "NUMERIC(6, 2)")
        add_product_column("vat_rate", "NUMERIC(6, 2)")
        add_product_column("shipping_fee", "NUMERIC(12, 2)")


def get_session() -> Iterator[Session]:
    """Provide a database session for FastAPI dependencies.

    This generator is designed for FastAPI's dependency system, which expects a
    ``yield``-based lifecycle. Using ``@contextmanager`` here would return a
    context manager object instead of the actual ``Session`` instance, causing
    request handlers to receive the wrong type. The explicit ``yield`` keeps the
    session lifecycle readable while ensuring commits and rollbacks happen in a
    single place.
    """

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
