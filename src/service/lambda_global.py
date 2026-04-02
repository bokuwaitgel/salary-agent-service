import json
import re
import urllib.parse
import asyncio
import requests
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import datetime
from pydantic import ValidationError
from schemas.database.lambda_jobs import LambdaJobSchema
from src.logger import logger

#get detail url 


def extract_jobs_list_from_html(html_content) -> list[dict]:
    """Extract job listings from saved HTML file."""
    soup = html_content
    jobs = []

    for a_tag in soup.find_all("a", href=True):
        job_link = str(a_tag["href"]) if a_tag["href"] else ""
        
        if not job_link.startswith("/jobs/"):
            continue
        
        # Extract the full slug (e.g., "uil-ajillagaa-hariutssan-erunhii-menejer-61181709")
        slug_match = re.search(r"/jobs/([^/?]+)", job_link)
        slug = slug_match.group(1) if slug_match else None
        
        # Extract the numeric job_id from the end of the slug (e.g., "61181709")
        job_id_match = re.search(r"-(\d+)$", slug) if slug else None


        jobs.append({
            "job_id": job_id_match.group(1) if job_id_match else None,
            "slug": slug,
            "job_link": urllib.parse.urljoin("https://www.lambda.global", job_link),
            "job_title": a_tag.get_text(strip=True)
        })
    
    return jobs

async def fetch_jobs_with_playwright(url: str, max_retries: int = 3) -> list[dict]:
    """Fetch job listings using Playwright and parse them."""


    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for attempt in range(max_retries):
            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                # Wait for job links to appear in the DOM
                await page.wait_for_selector("a[href^='/jobs/']", timeout=15000)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning("Attempt %s failed for %s: %s. Retrying...", attempt + 1, url, e)
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error("All %s attempts failed for %s: %s", max_retries, url, e)
                    await browser.close()
                    return []

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        await browser.close()

    return extract_jobs_list_from_html(soup)

def get_job_detail_from_request(job_url: str, max_retries: int = 3) -> dict:
    """Fetch job detail using requests with retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(job_url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
            else:
                print(f"Failed after {max_retries} attempts: {job_url}: {e}")
                return {}
    return {}

async def get_all_data_and_save(repository):
    url = "https://lambda.global/jobs?minSalary=1000000&maxSalary=20000000&sortBy=newest&page="
    now = datetime.datetime.now(datetime.timezone.utc)
    current_year = str(now.year)
    current_month = f"{now.month:02d}"

    def _to_optional_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    def _to_optional_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    result_jobs = []
    page=1
    while True:
        full_url = f"{url}{page}"
        logger.info("Fetching Lambda jobs from: %s", full_url)
        jobs = await fetch_jobs_with_playwright(full_url)
        logger.info("Extracted %s Lambda jobs on page %s", len(jobs), page)
        if not jobs:
            break
        page += 1
        result_jobs.extend(jobs)
        
    logger.info("Total Lambda jobs discovered: %s", len(result_jobs))
    #get existing job ids
    existing_job_ids = repository.get_all_ids()
    logger.info("Existing Lambda job IDs in database: %s", len(existing_job_ids))
    
    # Filter jobs that need to be fetched
    jobs_to_fetch = [
        job for job in result_jobs 
        if job["job_id"] and f"{current_year}_{current_month}_{job['job_id']}" not in existing_job_ids
    ]
    logger.info("Lambda jobs to fetch details for: %s", len(jobs_to_fetch))
    
    # Fetch job details using ThreadPoolExecutor for batch processing
    new_jobs = []
    total = len(jobs_to_fetch)
    
    urls = [f"https://api.lambda.global/api/jobsPublic/{job['slug']}" for job in jobs_to_fetch]
    
    logger.info("Starting to fetch Lambda job details")
    # Use ThreadPoolExecutor with 5 workers for concurrent requests
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_job_detail_from_request, url) for url in urls]
        
        for idx, future in enumerate(futures):
            job_detail = future.result()
            if job_detail:
                new_jobs.append(job_detail)
            if (idx + 1) % 10 == 0 or idx + 1 == total:
                logger.info("Fetched Lambda details: %s/%s", idx + 1, total)
    
    logger.info("New Lambda jobs fetched from API: %s", len(new_jobs))
    
    # Transform API response to match schema
    transformed_jobs = []
    for job in new_jobs:
        recruiter = job.get("recruiter", {}) or {}
        salary = job.get("salary", {}) or {}
        transformed = {
            "id": _to_optional_str(f"{job.get('id')}") if job.get("id") is not None else None,
            "title": _to_optional_str(job.get("title")),
            "description": _to_optional_str(job.get("description")),
            "location": _to_optional_str(job.get("location")),
            "company_name": _to_optional_str(recruiter.get("company")),
            "company_name_mn": _to_optional_str(recruiter.get("companyMn")),
            "salary_min": _to_optional_int(salary.get("min")),
            "salary_max": _to_optional_int(salary.get("max")),
            "salary_type": _to_optional_str(salary.get("type")),
            "position_type": _to_optional_str(job.get("positionType")),
            "engagement_type": _to_optional_str(job.get("engagmentType")),
            "pay_type": _to_optional_str(job.get("payType")),
            "experience": _to_optional_int(job.get("experience")),
            "responsibilities": _to_optional_str(job.get("responsibilities")),
            "skills": json.dumps(job.get("skills", []), ensure_ascii=False) if job.get("skills") else None,
            "commitment": _to_optional_str(job.get("commitment")),
            "job_category_id": _to_optional_int(job.get("jobCategoryId")),
            "deadline": job.get("deadline"),
            "slug": _to_optional_str(job.get("slug")),
            "view_count": _to_optional_int(job.get("viewCount")),
            "apply_count": _to_optional_int(job.get("applyCount")),
            "recruiter_id": _to_optional_int(job.get("recruiterId")),
            "recruiter_company": _to_optional_str(recruiter.get("company")),
            "recruiter_industry": _to_optional_str(recruiter.get("industry")),
            "recruiter_location": _to_optional_str(recruiter.get("location")),
            "recruiter_verified": 1 if recruiter.get("verified") else 0,
            "tags": json.dumps([tag.get("nameMn") for tag in job.get("tags", []) if tag.get("nameMn")], ensure_ascii=False) if job.get("tags") else None,
            "status": _to_optional_str(job.get("status")),
            "year": current_year,
            "month": current_month,
            "api_created_at": job.get("createdAt"),
            "api_updated_at": job.get("updatedAt"),
        }
        transformed_jobs.append(transformed)
    
    # validate + save new jobs in batch
    valid_jobs: list[LambdaJobSchema] = []
    invalid_count = 0
    for job in transformed_jobs:
        try:
            valid_jobs.append(LambdaJobSchema(**job))
        except ValidationError:
            invalid_count += 1
            logger.exception("Skipping invalid Lambda job payload: %s", job.get("id"))

    inserted = 0
    if valid_jobs:
        inserted_rows = repository.batch_create(valid_jobs)
        inserted = len(inserted_rows)

    result = {
        "fetched": len(result_jobs),
        "new": len(jobs_to_fetch),
        "inserted": inserted,
        "invalid": invalid_count,
    }
    logger.info("Lambda sync result: %s", result)
    return result
