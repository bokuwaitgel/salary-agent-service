from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, List, Union
from sqlalchemy.orm import Session

from schemas.zangia_jobs import ZangiaJobTable
from schemas.lambda_jobs import LambdaJobTable

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
        all_db_objs = []
        
        for i in range(0, len(objs_in), chunk_size):
            chunk = objs_in[i:i + chunk_size]
            db_objs = []
            for obj_in in chunk:
                data = obj_in.model_dump(exclude_none=True)
                if not data.get("id"):
                    raise ValueError("ZangiaJob requires non-empty `id` (mapped from API `code`).")
                db_obj = ZangiaJobTable(**data)
                self.db_session.add(db_obj)
                db_objs.append(db_obj)
            self.db_session.commit()
            all_db_objs.extend(db_objs)
            print(f"Inserted chunk {i // chunk_size + 1} ({len(chunk)} records)")
        
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
        all_db_objs = []
        skipped = 0
        
        for i in range(0, len(objs_in), chunk_size):
            chunk = objs_in[i:i + chunk_size]
            db_objs = []
            for obj_in in chunk:
                data = obj_in.model_dump(exclude_none=True)
                if not data.get("id"):
                    raise ValueError("LambdaJob requires non-empty `id`.")
                
                # Check if already exists
                existing = self.db_session.query(LambdaJobTable).filter(LambdaJobTable.id == data["id"]).first()
                if existing:
                    skipped += 1
                    continue
                    
                db_obj = LambdaJobTable(**data)
                self.db_session.add(db_obj)
                db_objs.append(db_obj)
            self.db_session.commit()
            all_db_objs.extend(db_objs)
            print(f"Inserted chunk {i // chunk_size + 1} ({len(db_objs)} records, skipped {skipped} duplicates)")
        
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