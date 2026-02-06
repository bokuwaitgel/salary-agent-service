from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

from schemas.zangia_jobs import Base as ZangiaBase, ZangiaJobTable
from schemas.lambda_jobs import Base as LambdaBase, LambdaJobTable
from src.repositories.database import ZangiaJobRepository, LambdaJobRepository

load_dotenv()


def _get_engine():
    """Create and return a SQLAlchemy engine with connection pooling."""
    conn_str = os.getenv("DATABASE_URI", "sqlite:///products.db")
    return create_engine(
        conn_str,
        pool_pre_ping=True,  # Check connection health before using
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,  # Recycle connections every 5 minutes
    )


def get_zangia_sqlalchemy_repository():
    """Get Zangia job repository."""
    engine = _get_engine()
    ZangiaBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return ZangiaJobRepository(Session())


def get_lambda_sqlalchemy_repository():
    """Get Lambda Global job repository."""
    engine = _get_engine()
    LambdaBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return LambdaJobRepository(Session())