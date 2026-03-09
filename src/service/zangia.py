from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import requests
from pydantic import BaseModel

from schemas.database.zangia_jobs import ZangiaJobSchema, ZangiaJobTable
from src.logger import logger
from src.repositories.database import ZangiaJobRepository

class ZangiaDBService:
    def __init__(self, repository: ZangiaJobRepository):
        self.repository = repository

    def get_job_by_id(self, job_id: str) -> Optional[BaseModel]:
        return self.repository.get_by_id(job_id)
    
    def get_jobs_by_query(self, query: Any) -> Sequence[BaseModel]:
        return self.repository.get_query(query)

    def get_all_jobs(self) -> List[Any]:
        return self.repository.get_all()

    def create_job(self, job_data: BaseModel) -> BaseModel:
        return self.repository.create(job_data)

    def update_job(self, job_id: str, job_data: BaseModel) -> BaseModel:
        return self.repository.update(job_id, job_data)

    def delete_job(self, job_id: str) -> None:
        self.repository.delete(job_id)

    def batch_create_jobs(self, jobs_data: List[BaseModel]) -> Sequence[BaseModel]:
        return self.repository.batch_create(jobs_data)



#https://new-api.zangia.mn/api/jobs/search?limit=250&timetypeId%5B%5D=1&addrId%5B%5D=1&postDate=4&time=1
URL = "https://new-api.zangia.mn/api/jobs/search"
DEFAULT_TIMEOUT = 30

class ZangiaService:
    def __init__(self, repository: ZangiaJobRepository, timeout: int = DEFAULT_TIMEOUT):
        self.db_service = ZangiaDBService(repository)
        self.repository = repository
        self.url = URL
        self.timeout = timeout

    @staticmethod
    def _to_optional_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    def _extract_data_from_list(self, input_list: List[dict]) -> List[Dict[str, Any]]:
        """Extract specific fields from a list of job dictionaries."""
        extracted_info: List[Dict[str, Any]] = []

        for item in input_list:
            time_value = item.get("time")
            if time_value:
                start_on = datetime.fromtimestamp(time_value, tz=timezone.utc)
            else:
                start_on = datetime.now(timezone.utc)

            dict_item = {
                "code": self._to_optional_str(item.get("code")),
                "address": self._to_optional_str(item.get("address")),
                "age_requires": self._to_optional_str(item.get("age_requires")),
                "company_name": self._to_optional_str(item.get("company_name")),
                "company_name_en": self._to_optional_str(item.get("company_name_en")),
                "company_id": self._to_optional_str(item.get("company_id")),
                "job_level": item.get("job_level"),
                "job_level_id": item.get("job_level_id"),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "search_additional": self._to_optional_str(item.get("search_additional")),
                "search_description": self._to_optional_str(item.get("search_description")),
                "search_main": self._to_optional_str(item.get("search_main")),
                "search_requirements": self._to_optional_str(item.get("search_requirements")),
                "timetype": self._to_optional_str(item.get("timetype")),
                "is_active": True,
                "start_on": start_on,
                "title": self._to_optional_str(item.get("title")),
            }
            extracted_info.append(dict_item)

        return extracted_info

    def fetch_jobs(
        self,
        page: int = 1,
        limit: int = 250,
        post_date: int = 4, # last 30 days
        time_type: int = 1,
        timetype_ids: Optional[List[int]] = None,
        addr_ids: Optional[List[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch job listings from Zangia API with pagination."""
        params = {
            "limit": limit,
            "page": page,
            "postDate": post_date,
            "time": time_type,
            "timetypeId[]": timetype_ids or [1],
            "addrId[]": addr_ids or [1],
        }

        try:
            response = requests.get(self.url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            logger.exception("Failed to fetch Zangia jobs page=%s", page)
            return None
        except ValueError:
            logger.exception("Invalid JSON in Zangia response page=%s", page)
            return None

    def get_jobs_using_api(self, limit: int = 250) -> List[Dict[str, Any]]:
        """Fetch all pages from Zangia API and return normalized job dictionaries."""
        first_page = self.fetch_jobs(page=1, limit=limit)
        if not first_page:
            return []

        total_pages = int((first_page.get("meta") or {}).get("totalPages", 1) or 1)
        all_extracted_data: List[Dict[str, Any]] = []

        for page in range(1, total_pages + 1):
            jobs_page = first_page if page == 1 else self.fetch_jobs(page=page, limit=limit)
            if not jobs_page:
                continue

            items = jobs_page.get("items", [])
            all_extracted_data.extend(self._extract_data_from_list(items))

        now = datetime.now(timezone.utc)
        current_year = str(now.year)
        current_month = f"{now.month:02d}"
        for job in all_extracted_data:
            job["year"] = current_year
            job["month"] = current_month

        logger.info(
            "Zangia fetched %s jobs from %s pages",
            len(all_extracted_data),
            total_pages,
        )
        return all_extracted_data

    def gather_and_save(self, limit: int = 250) -> Dict[str, int]:
        """Fetch all jobs from API and persist only new records."""
        all_jobs = self.get_jobs_using_api(limit=limit)
        if not all_jobs:
            logger.info("No Zangia jobs fetched from API")
            return {"fetched": 0, "new": 0, "inserted": 0, "duplicates": 0}

        existing_jobs = self.repository.get_all()
        existing_job_ids = {job.id for job in existing_jobs}

        new_jobs = [job for job in all_jobs if job.get("code") not in existing_job_ids]

        seen_codes = set()
        jobs_to_create: List[BaseModel] = []
        duplicates_in_batch = 0
        for job in new_jobs:
            job_code = job.get("code")
            if not job_code:
                continue
            if job_code in seen_codes:
                duplicates_in_batch += 1
                continue
            seen_codes.add(job_code)
            jobs_to_create.append(ZangiaJobSchema(**job))

        inserted = 0
        if jobs_to_create:
            self.repository.batch_create(jobs_to_create)
            inserted = len(jobs_to_create)

        result = {
            "fetched": len(all_jobs),
            "new": len(new_jobs),
            "inserted": inserted,
            "duplicates": duplicates_in_batch,
        }
        logger.info("Zangia sync result: %s", result)
        return result
    
    def gather_and_save_update(self, limit: int = 250) -> Dict[str, int]:
        """Fetch all jobs from API and persist new records, update existing ones."""
        active_jobs = self.repository.get_query(ZangiaJobTable.is_active == True)
        active_job_ids: set[str] = {str(job.id) for job in active_jobs}

        all_jobs = self.get_jobs_using_api(limit=limit)
        if not all_jobs:
            logger.info("No Zangia jobs fetched from API")
            return {"fetched": 0, "new": 0, "updated": 0, "duplicates": 0}

        existing_jobs = self.repository.get_all()
        existing_jobs_dict = {str(job.id): job for job in existing_jobs}

        new_jobs = []
        updated_jobs = []
        duplicates_in_batch = 0
        seen_codes = set()

        for job in all_jobs:
            job_code = job.get("code")
            if not job_code:
                continue
            if job_code in seen_codes:
                duplicates_in_batch += 1
                continue
            seen_codes.add(job_code)

            existing_job = existing_jobs_dict.get(job_code)
            if existing_job:
                for field, value in job.items():
                    setattr(existing_job, field, value)
                updated_jobs.append(existing_job)
            else:
                new_jobs.append(ZangiaJobSchema(**job))

        if new_jobs:
            self.repository.batch_create(new_jobs)
                
        jobs = updated_jobs + new_jobs
        
        # active_job_ids - new_jobs = un active jobs, so we need to mark them as inactive
        active_job_codes = {job.code for job in jobs}
        for job_id in active_job_ids:
            if job_id not in active_job_codes:
                job_to_update = existing_jobs_dict.get(job_id)
                if job_to_update:
                    setattr(job_to_update, "is_active", False)
                    self.repository.update(str(job_id), job_to_update)
                    updated_jobs.append(job_to_update)
        
        result = {
            "fetched": len(all_jobs),
            "new": len(new_jobs),
            "updated": len(updated_jobs),
            "duplicates": duplicates_in_batch,
        }
        logger.info("Zangia sync with update result: %s", result)
        return result