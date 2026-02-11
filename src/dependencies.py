from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

from schemas.database.zangia_jobs import Base as ZangiaBase, ZangiaJobTable
from schemas.database.lambda_jobs import Base as LambdaBase, LambdaJobTable
from schemas.database.base_classifier_db import Base as ClassifierBase, JobClassificationOutputTable
from schemas.database.salary_calculation_db import Base as SalaryCalculationBase, SalaryCalculationOutputTable
from src.repositories.database import SalaryCalculationOutputRepository, ZangiaJobRepository, LambdaJobRepository, JobClassificationOutputRepository

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
    ZangiaBase.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    return ZangiaJobRepository(Session())


def get_lambda_sqlalchemy_repository():
    """Get Lambda Global job repository."""
    engine = _get_engine()
    LambdaBase.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    return LambdaJobRepository(Session())

def get_classifier_output_repository():
    """Get repository for job classification output."""
    engine = _get_engine()
    ClassifierBase.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    return JobClassificationOutputRepository(Session())

def get_salary_calculation_output_repository():
    """Get repository for salary calculation output."""
    engine = _get_engine()
    SalaryCalculationBase.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    return SalaryCalculationOutputRepository(Session())