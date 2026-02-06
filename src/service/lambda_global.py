import json
import re
import urllib.parse
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from schemas.lambda_jobs import LambdaJobSchema

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

async def fetch_jobs_with_playwright(url: str) -> list[dict]:
    """Fetch job listings using Playwright and parse them."""

    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
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
    url = "https://lambda.global/jobs?minSalary=1000000&maxSalary=15000000&page="
    result_jobs = []
    page=1
    while True:
        full_url = f"{url}{page}"
        print(f"Fetching jobs from: {full_url}")
        jobs = await fetch_jobs_with_playwright(full_url)
        print(f"Extracted {len(jobs)} jobs:")
        if not jobs:
            break
        page += 1
        result_jobs.extend(jobs)
        
    print(f"Total jobs so far: {len(result_jobs)}")
    #get existing job ids
    existing_job_ids = repository.get_all_ids()
    print(f"Existing job IDs in database: {len(existing_job_ids)}")
    
    # Filter jobs that need to be fetched
    jobs_to_fetch = [
        job for job in result_jobs 
        if job["job_id"] and int(job["job_id"]) not in existing_job_ids
    ]
    print(f"Jobs to fetch details for: {len(jobs_to_fetch)}")
    
    # Fetch job details using ThreadPoolExecutor for batch processing
    new_jobs = []
    total = len(jobs_to_fetch)
    
    urls = [f"https://api.lambda.global/api/jobsPublic/{job['slug']}" for job in jobs_to_fetch]
    
    print("Starting to fetch job details...")
    # Use ThreadPoolExecutor with 5 workers for concurrent requests
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_job_detail_from_request, url) for url in urls]
        
        for idx, future in enumerate(futures):
            job_detail = future.result()
            if job_detail:
                new_jobs.append(job_detail)
            if (idx + 1) % 10 == 0 or idx + 1 == total:
                print(f"Fetched: {idx + 1}/{total} jobs...")
    
    print(f"New jobs to be added: {len(new_jobs)}")
    
    # Transform API response to match schema
    transformed_jobs = []
    for job in new_jobs:
        recruiter = job.get("recruiter", {}) or {}
        salary = job.get("salary", {}) or {}
        transformed = {
            "id": job.get("id"),
            "title": job.get("title"),
            "description": job.get("description"),
            "location": job.get("location"),
            "company_name": recruiter.get("company"),
            "company_name_mn": recruiter.get("companyMn"),
            "salary_min": salary.get("min"),
            "salary_max": salary.get("max"),
            "salary_type": salary.get("type"),
            "position_type": job.get("positionType"),
            "engagement_type": job.get("engagmentType"),
            "pay_type": job.get("payType"),
            "experience": job.get("experience"),
            "responsibilities": job.get("responsibilities"),
            "skills": json.dumps(job.get("skills", []), ensure_ascii=False) if job.get("skills") else None,
            "commitment": job.get("commitment"),
            "job_category_id": job.get("jobCategoryId"),
            "deadline": job.get("deadline"),
            "slug": job.get("slug"),
            "view_count": job.get("viewCount"),
            "apply_count": int(job.get("applyCount", 0)) if job.get("applyCount") else None,
            "recruiter_id": job.get("recruiterId"),
            "recruiter_company": recruiter.get("company"),
            "recruiter_industry": recruiter.get("industry"),
            "recruiter_location": recruiter.get("location"),
            "recruiter_verified": 1 if recruiter.get("verified") else 0,
            "tags": json.dumps([tag.get("nameMn") for tag in job.get("tags", []) if tag.get("nameMn")], ensure_ascii=False) if job.get("tags") else None,
            "status": job.get("status"),
            "api_created_at": job.get("createdAt"),
            "api_updated_at": job.get("updatedAt"),
        }
        transformed_jobs.append(transformed)
    
    #save new jobs in batch
    repository.batch_create([LambdaJobSchema(**job) for job in transformed_jobs])
    print(f"Saved {len(transformed_jobs)} new jobs to the database.")
