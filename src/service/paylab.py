import os
import json
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def extract_salary_range(content):
    """Extract min and max salary from salary info box."""
    salary_div = content.find("div", class_="box-gray text-large")
    if not salary_div:
        return 0, 0
    
    salary_spans = salary_div.find_all("span", class_="text-nowrap")
    if len(salary_spans) < 2:
        return 0, 0
    
    try:
        min_salary = int(salary_spans[0].get_text(strip=True)
                        .replace('MNT', '').replace(',', '').strip())
        max_salary = int(salary_spans[1].get_text(strip=True)
                        .replace('MNT', '').replace(',', '').strip())
        return min_salary, max_salary
    except (ValueError, AttributeError):
        return 0, 0


def extract_job_listings(content):
    """Extract individual job listings from page content."""
    jobs = []
    
    for a_tag in content.find_all("a", href=True):
        job_link = a_tag["href"]
        
        # Filter only job listing links
        if not job_link.startswith("https://www.paylab.com/mn/salaryinfo/"):
            continue
        
        job = {"job_url": job_link}
        
        # Extract category name
        category_div = a_tag.find("div", class_="col-12 col-md-7")
        if category_div:
            job["category_name"] = category_div.get_text(strip=True)
        
        # Extract average salary
        salary_span = a_tag.find("span", style="white-space: nowrap;")
        if salary_span:
            job["average_salary"] = salary_span.get_text(strip=True)
        
        jobs.append(job)
    
    return jobs


def extract_jobs_from_html(content):
    """Extract all job information from HTML content."""
    min_salary, max_salary = extract_salary_range(content)
    job_listings = extract_job_listings(content)
    
    return {
        "min_salary": min_salary,
        "max_salary": max_salary,
        "job_urls": job_listings,
    }


def fetch_page_with_playwright(url, name):
    """Fetch webpage using Playwright and extract job data."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/143.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Save screenshot
        os.makedirs("images", exist_ok=True)
        page.screenshot(path=f"images/paylab_{name}.png", full_page=True)
        
        # Parse and save HTML
        html_content = BeautifulSoup(page.content(), "html.parser")
        os.makedirs("htmls", exist_ok=True)
        with open(f"htmls/paylab_{name}.html", "w", encoding="utf-8") as f:
            f.write(html_content.prettify())
        
        browser.close()
        
        return extract_jobs_from_html(html_content)


def main():
    """Main execution function."""
    url = "https://www.paylab.com/mn/salaryinfo"
    job_data = fetch_page_with_playwright(url, "paylab")
    
    # Save results to JSON
    os.makedirs("data", exist_ok=True)
    with open("data/paylab_job_urls.json", "w", encoding="utf-8") as f:
        json.dump(job_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()