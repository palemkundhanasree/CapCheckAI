import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

# Connect args specific to SQLite for multithreaded FastAPI handling
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
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

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # Seed default local demo admin
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(
            (User.username == "admin") | (User.email == "admin@capcheck.ai") | (User.email == "admin@truthlens.ai")
        ).first()
        if not existing_admin:
            admin_user = User(
                email="admin@capcheck.ai",
                username="admin",
                name="Administrator",
                hashed_password=get_password_hash("capcheck123"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default local admin created: admin@capcheck.ai")
        elif existing_admin.email == "admin@truthlens.ai":
            existing_admin.email = "admin@capcheck.ai"
            db.commit()
    except Exception as e:
        logger.error(f"Error seeding default admin user: {e}")
        db.rollback()
    finally:
        db.close()

