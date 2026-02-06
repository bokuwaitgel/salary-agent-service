import requests
from typing import Any, Dict, Iterable, Optional, List, Sequence
import json

from typing import List
from pydantic import BaseModel
from schemas.zangia_jobs import ZangiaJobSchema
from src.repositories.database import ZangiaJobRepository

class ZangiaDBService:
    def __init__(self, repository: ZangiaJobRepository):
        self.repository = repository

    def get_job_by_id(self, job_id: str) -> Optional[BaseModel]:
        return self.repository.get_by_id(job_id)

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

def fetch_job_listings(
        page: int = 1,
        limit: int =250
):
    """Fetch job listings from Zangia API with pagination."""
    params = {
        "limit": limit,
        "page": page,
        "postDate": 4,  # Last 24 hours
        "time": 1,       # Full-time jobs
        "timetypeId[]": 1,  # Permanent jobs
        "addrId[]": 1       # Ulaanbaatar
    }
    response = requests.get(URL, params=params)
    if response.status_code == 200:
        job_data = response.json()
        return job_data
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

def extract_data_from_list(input_list : List[dict]):
    """Extract specific fields from a list of job dictionaries."""
    extracted_info = []
    for item in input_list:
        dict_item = {
            "code": item.get("code"),
            "company_name": item.get("company_name"),
            "company_name_en": item.get("company_name_en"),
            "job_level": item.get("job_level"),
            "job_level_id": item.get("job_level_id"),
            "salary_min": item.get("salary_min"),
            "salary_max": item.get("salary_max"),
            "search_additional": item.get("search_additional"),
            "search_description": item.get("search_description"),
            "search_main": item.get("search_main"),
            "search_requirements": item.get("search_requirements"),
            "timetype": item.get("timetype"),
            "title": item.get("title"),
        }

        extracted_info.append(dict_item)

    return extracted_info


def get_jobs_using_api():
    """
    Fetch job listings from Zangia API and return the extracted data.
    That have pages and total count
    """
    #first page that to find total pages, total count
    jobs = fetch_job_listings()
    if not jobs:
        return None
    meta = jobs.get("meta", {})
    total_pages = meta.get("totalPages", 1)
    all_extracted_data = []
    for page in range(1, total_pages + 1):
        jobs_page = fetch_job_listings(page=page)
        if jobs_page:
            items = jobs_page.get("items", [])
            extracted = extract_data_from_list(items)
            all_extracted_data.extend(extracted)

    print(f"Total pages to fetch: {total_pages}")
    
    # if total pages is 1, we already have the data otherwise we fetched all pages
    for page in range(2, total_pages + 1):
        print(f"Fetching page {page} of {total_pages}")
        jobs_page = fetch_job_listings(page=page)
        if jobs_page:
            items = jobs_page.get("items", [])
            extracted = extract_data_from_list(items)
            all_extracted_data.extend(extracted)

    return all_extracted_data

def get_all_data_and_save(repository: ZangiaJobRepository):
    """
    Fetch all job listings from Zangia API and save them to the database.
    """
    all_jobs = get_jobs_using_api()
    if not all_jobs:
        print("No jobs fetched from API.")
        return
    

    #find existing job codes in the database
    existing_jobs = repository.get_all()
    print(f"Existing jobs in DB: {len(existing_jobs)}")
    existing_job_codes = {job.id for job in existing_jobs}
    print(f"Existing job codes in DB: {len(existing_job_codes)}")
    none_existing_jobs = [job for job in all_jobs if job.get("code") not in existing_job_codes]
    print(f"New jobs to add: {len(none_existing_jobs)}")
    
    # Deduplicate within the batch to avoid duplicate key errors
    seen_codes = set()
    jobs_to_create = []
    duplicates_in_batch = 0
    for job in none_existing_jobs:
        job_code = job.get("code")
        if job_code not in seen_codes:
            seen_codes.add(job_code)
            job_model = ZangiaJobSchema(**job)
            jobs_to_create.append(job_model)
        else:
            duplicates_in_batch += 1
    
    print(f"Duplicates found in batch: {duplicates_in_batch}")
    print(f"Unique jobs to insert: {len(jobs_to_create)}")
    
    if jobs_to_create:
        repository.batch_create(jobs_to_create)

    print(f"Saved {len(none_existing_jobs)} jobs to the database.")

    #update other existing jobs
    # for job in all_jobs:
    #     if job.get("code") in existing_job_codes:
    #         job_model = ZangiaJobSchema(**job)
    #         if job_model.id is not None:
    #             repository.update(job_model.id, job_model)



