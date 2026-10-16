import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings, normalize_database_url

logger = logging.getLogger(__name__)

# Ensure database URL is normalized to an absolute path so SQLite can always open it
database_url = normalize_database_url(settings.DATABASE_URL)

# Connect args specific to SQLite for multithreaded FastAPI handling
connect_args = {"check_same_thread": False, "timeout": 30} if database_url.startswith("sqlite") else {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates database tables and seeds default admin user."""
    from app.db.models import User
    from app.security.authentication import get_password_hash

    if database_url.startswith("sqlite:"):
        from pathlib import Path
        raw = database_url
        for prefix in ["sqlite:////", "sqlite:///", "sqlite://", "sqlite:"]:
            if raw.startswith(prefix):
                raw = raw[len(prefix):]
                break
        if raw and raw != ":memory:":
            try:
                Path(raw).parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_columns()
    logger.info("Database tables initialized successfully.")

    # Seed default local demo admin
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter((User.username == "admin") | (User.email == "admin@truthlens.ai")).first()
        if not existing_admin:
            admin_user = User(
                email="admin@truthlens.ai",
                username="admin",
                name="Administrator",
                hashed_password=get_password_hash("capcheck123"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default local admin created.")
    except Exception as e:
        logger.error(f"Error seeding default admin user: {e}")
        db.rollback()
    finally:
        db.close()



def _migrate_sqlite_columns() -> None:
    """Adds columns introduced after the first release to an existing SQLite database."""
    if not database_url.startswith("sqlite"):
        return
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
            if cols and "otp_attempts" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN otp_attempts INTEGER DEFAULT 0"))
            rcols = {row[1] for row in conn.execute(text("PRAGMA table_info(reports)"))}
            if rcols and "correctness_score" not in rcols:
                conn.execute(text("ALTER TABLE reports ADD COLUMN correctness_score FLOAT"))
            if rcols and "correctness_explanation" not in rcols:
                conn.execute(text("ALTER TABLE reports ADD COLUMN correctness_explanation TEXT"))
            if rcols and "report_card" not in rcols:
                conn.execute(text("ALTER TABLE reports ADD COLUMN report_card TEXT"))
    except Exception as e:  # pragma: no cover
        logger.error(f"Schema migration failed: {e}")
