from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from schemas.database.zangia_jobs import ZangiaJobTable
from schemas.database.lambda_jobs import LambdaJobTable
from schemas.database.base_classifier_db import JobClassificationOutputTable
from schemas.database.salary_calculation_db import SalaryCalculationOutputTable
from schemas.database.user import UserTable

logger = logging.getLogger(__name__)

class DatabaseRepository(ABC):
    def __init__(self, db_session: Session):
        self.db_session = db_session

    @abstractmethod
    def get_by_id(self, record_id: str) -> Any:
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        pass

    @abstractmethod
    def create(self, obj_in: BaseModel) -> Any:
        pass

    @abstractmethod
    def update(self, record_id: str, obj_in: BaseModel) -> Any:
        pass

    @abstractmethod
    def delete(self, record_id: str) -> None:
        pass

class ZangiaJobRepository(DatabaseRepository):
    def get_by_id(self, record_id: str) -> ZangiaJobTable:
        return self.db_session.query(ZangiaJobTable).filter(ZangiaJobTable.id == record_id).first()

    def get_all(self) -> List[ZangiaJobTable]:
        return self.db_session.query(ZangiaJobTable).all()
    
    def get_query(self, query) -> List[ZangiaJobTable]:
        return self.db_session.query(ZangiaJobTable).filter(query).all()

    def create(self, obj_in: BaseModel) -> ZangiaJobTable:
        data = obj_in.model_dump(exclude_none=True)
        if not data.get("id"):
            raise ValueError("ZangiaJob requires non-empty `id` (mapped from API `code`).")
        db_obj = ZangiaJobTable(**data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj
    
    def batch_create(self, objs_in: List[BaseModel], chunk_size: int = 100) -> List[ZangiaJobTable]:
        """Insert records in chunks to avoid connection timeouts."""
        all_db_objs: List[ZangiaJobTable] = []

        for i in range(0, len(objs_in), chunk_size):
            chunk = objs_in[i:i + chunk_size]
            db_objs: List[ZangiaJobTable] = []
            try:
                for obj_in in chunk:
                    data = obj_in.model_dump(exclude_none=True)
                    if not data.get("id"):
                        raise ValueError("ZangiaJob requires non-empty `id` (mapped from API `code`).")
                    db_obj = ZangiaJobTable(**data)
                    self.db_session.add(db_obj)
                    db_objs.append(db_obj)
                self.db_session.commit()
                all_db_objs.extend(db_objs)
                logger.info("Zangia chunk %d: inserted %d records", i // chunk_size + 1, len(db_objs))
            except Exception:
                self.db_session.rollback()
                logger.exception("Zangia chunk %d failed – rolled back", i // chunk_size + 1)
                raise

        return all_db_objs

    def update(self, record_id: str, obj_in: BaseModel) -> ZangiaJobTable:
        db_obj = self.get_by_id(record_id)
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj

    def delete(self, record_id: str) -> None:
        db_obj = self.get_by_id(record_id)
        self.db_session.delete(db_obj)
        self.db_session.commit()


class LambdaJobRepository(DatabaseRepository):
    def get_by_query(self, query) -> List[LambdaJobTable]:
        return self.db_session.query(LambdaJobTable).filter(query).all()

    def get_by_id(self, record_id: int) -> LambdaJobTable:
        return self.db_session.query(LambdaJobTable).filter(LambdaJobTable.id == record_id).first()

    def get_all(self) -> List[LambdaJobTable]:
        return self.db_session.query(LambdaJobTable).all()
    
    def get_all_ids(self) -> set:
        """Get all job IDs efficiently without loading full objects."""
        results = self.db_session.query(LambdaJobTable.id).all()
        return {r[0] for r in results}

    def create(self, obj_in: BaseModel) -> LambdaJobTable:
        data = obj_in.model_dump(exclude_none=True)
        if not data.get("id"):
            raise ValueError("LambdaJob requires non-empty `id`.")
        db_obj = LambdaJobTable(**data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        return db_obj
    
    def batch_create(self, objs_in: List[BaseModel], chunk_size: int = 100) -> List[LambdaJobTable]:
        """Insert records in chunks, skipping duplicates."""
        all_db_objs: List[LambdaJobTable] = []
        skipped = 0

        # Pre-fetch existing IDs to avoid N+1 per-item queries
        existing_ids = self.get_all_ids()

        for i in range(0, len(objs_in), chunk_size):
            chunk = objs_in[i:i + chunk_size]
            db_objs: List[LambdaJobTable] = []
            try:
                for obj_in in chunk:
                    data = obj_in.model_dump(exclude_none=True)
                    if not data.get("id"):
                        raise ValueError("LambdaJob requires non-empty `id`.")
                    if data["id"] in existing_ids:
                        skipped += 1
                        continue
                    db_obj = LambdaJobTable(**data)
                    self.db_session.add(db_obj)
                    db_objs.append(db_obj)
                    existing_ids.add(data["id"])
                self.db_session.commit()
                all_db_objs.extend(db_objs)
                logger.info("Lambda chunk %d: inserted %d, skipped %d duplicates",
                            i // chunk_size + 1, len(db_objs), skipped)
            except Exception:
                self.db_session.rollback()
                logger.exception("Lambda chunk %d failed – rolled back", i // chunk_size + 1)
                raise

        return all_db_objs

    def update(self, record_id: int, obj_in: BaseModel) -> LambdaJobTable:
        db_obj = self.get_by_id(record_id)
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db_session.commit()
        return db_obj

    def delete(self, record_id: int) -> None:
        db_obj = self.get_by_id(record_id)
        self.db_session.delete(db_obj)
        self.db_session.commit()


class JobClassificationOutputRepository(DatabaseRepository):
    def get_by_id(self, record_id: int) -> JobClassificationOutputTable:
        return self.db_session.query(JobClassificationOutputTable).filter(JobClassificationOutputTable.id == record_id).first()

    def get_by_query(self, query) -> List[JobClassificationOutputTable]:
        return self.db_session.query(JobClassificationOutputTable).filter(query).all()

    def get_all(self) -> List[JobClassificationOutputTable]:
        return self.db_session.query(JobClassificationOutputTable).all()

    def create(self, obj_in: dict) -> JobClassificationOutputTable:
        #check id exists
        if not obj_in.get("id"):
            raise ValueError("JobClassificationOutput requires non-empty `id`.")

        check_existing = self.get_by_id(obj_in["id"])
        if check_existing:
            logger.debug("JobClassificationOutput id=%s already exists – skipping", obj_in["id"])
            return check_existing

        data = obj_in.copy()
        db_obj = JobClassificationOutputTable(**data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        return db_obj

    def update(self, record_id: int, obj_in: BaseModel) -> JobClassificationOutputTable:
        db_obj = self.get_by_id(record_id)
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db_session.commit()
        return db_obj

    def delete(self, record_id: int) -> None:
        db_obj = self.get_by_id(record_id)
        self.db_session.delete(db_obj)
        self.db_session.commit()



class SalaryCalculationOutputRepository(DatabaseRepository):
    def get_by_id(self, record_id: int) -> SalaryCalculationOutputTable:
        return self.db_session.query(SalaryCalculationOutputTable).filter(SalaryCalculationOutputTable.id == record_id).first()

    def get_all(self) -> List[SalaryCalculationOutputTable]:
        return self.db_session.query(SalaryCalculationOutputTable).all()
    
    def get_by_type(self, type_value: str) -> List[SalaryCalculationOutputTable]:
        return self.db_session.query(SalaryCalculationOutputTable).filter(SalaryCalculationOutputTable.type == type_value).all()

    def check_exists(self, obj: dict) -> Union[SalaryCalculationOutputTable, None]:
        #check year, month, title, type exists
        return self.db_session.query(SalaryCalculationOutputTable).filter(
            SalaryCalculationOutputTable.year == obj.get("year"),
            SalaryCalculationOutputTable.month == obj.get("month"),
            SalaryCalculationOutputTable.title == obj.get("title"),
            SalaryCalculationOutputTable.type == obj.get("type"),
        ).first()
    

    def create(self, obj_in: dict) -> SalaryCalculationOutputTable:
        #check id exists
        check_existing = self.check_exists(obj_in)
        if check_existing:
            logger.debug("SalaryCalc record for %s (%s) %s/%s already exists – skipping",
                         obj_in.get("title"), obj_in.get("type"), obj_in.get("month"), obj_in.get("year"))
            return check_existing

        data = obj_in.copy()
        db_obj = SalaryCalculationOutputTable(**data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        return db_obj

    def upsert(self, obj_in: dict) -> SalaryCalculationOutputTable:
        existing = self.check_exists(obj_in)
        if existing:
            for field, value in obj_in.items():
                if field == "id":
                    continue
                if hasattr(existing, field):
                    setattr(existing, field, value)
            self.db_session.commit()
            return existing

        data = obj_in.copy()
        db_obj = SalaryCalculationOutputTable(**data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        return db_obj

    def update(self, record_id: int, obj_in: BaseModel) -> SalaryCalculationOutputTable:
        db_obj = self.get_by_id(record_id)
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db_session.commit()
        return db_obj

    def delete(self, record_id: int) -> None:
        db_obj = self.get_by_id(record_id)
        self.db_session.delete(db_obj)
        self.db_session.commit()


class UserRepository(DatabaseRepository):
    def get_by_id(self, record_id: str) -> Optional[UserTable]:
        return self.db_session.query(UserTable).filter(UserTable.id == record_id).first()

    def get_by_email(self, email: str) -> Optional[UserTable]:
        return self.db_session.query(UserTable).filter(UserTable.email == email).first()

    def get_all(self) -> List[UserTable]:
        return self.db_session.query(UserTable).all()

    def create(self, obj_in: dict) -> UserTable:
        db_obj = UserTable(**obj_in)
        self.db_session.add(db_obj)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj

    def update(self, record_id: str, obj_in: dict) -> Optional[UserTable]:
        db_obj = self.get_by_id(record_id)
        if not db_obj:
            return None

        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj

    def delete(self, record_id: str) -> None:
        db_obj = self.get_by_id(record_id)
        if not db_obj:
            return

        self.db_session.delete(db_obj)
        self.db_session.commit()




