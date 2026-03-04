from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from schemas.database.zangia_jobs import Base as ZangiaBase
from schemas.database.lambda_jobs import Base as LambdaBase
from schemas.database.base_classifier_db import Base as ClassifierBase
from schemas.database.salary_calculation_db import Base as SalaryCalculationBase
from src.repositories.database import (
    JobClassificationOutputRepository,
    LambdaJobRepository,
    SalaryCalculationOutputRepository,
    ZangiaJobRepository,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton engine + session factory
# ---------------------------------------------------------------------------
_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None
_TABLES_CREATED: set[str] = set()


def _get_engine() -> Engine:
    """Return a module-level singleton SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is None:
        conn_str = os.getenv("DATABASE_URI", "sqlite:///products.db")
        _ENGINE = create_engine(
            conn_str,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
        )
        logger.info("SQLAlchemy engine created: %s", conn_str.split("@")[-1] if "@" in conn_str else conn_str[:40])
    return _ENGINE


def _get_session_factory() -> sessionmaker[Session]:
    """Return a module-level singleton session factory."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=_get_engine())
    return _SESSION_FACTORY


def _ensure_tables(base, label: str) -> None:
    """Create tables once per base to avoid redundant DDL checks."""
    if label not in _TABLES_CREATED:
        base.metadata.create_all(_get_engine(), checkfirst=True)
        _TABLES_CREATED.add(label)


# ---------------------------------------------------------------------------
# Repository factories
# ---------------------------------------------------------------------------

def get_zangia_sqlalchemy_repository() -> ZangiaJobRepository:
    """Get Zangia job repository."""
    _ensure_tables(ZangiaBase, "zangia")
    return ZangiaJobRepository(_get_session_factory()())


def get_lambda_sqlalchemy_repository() -> LambdaJobRepository:
    """Get Lambda Global job repository."""
    _ensure_tables(LambdaBase, "lambda")
    return LambdaJobRepository(_get_session_factory()())


def get_classifier_output_repository() -> JobClassificationOutputRepository:
    """Get repository for job classification output."""
    _ensure_tables(ClassifierBase, "classifier")
    return JobClassificationOutputRepository(_get_session_factory()())


def get_salary_calculation_output_repository() -> SalaryCalculationOutputRepository:
    """Get repository for salary calculation output."""
    _ensure_tables(SalaryCalculationBase, "salary_calc")
    return SalaryCalculationOutputRepository(_get_session_factory()())