import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def extract_salary_range(content):
    """Extract min and max salary from salary div"""
    div = content.find("div", class_="d-flex align-self-stretch justify-content-between my-3")
    
    salary_data: dict[str, int | str | list | None] = {
        "min_salary": None,
        "max_salary": None,
        "min_salary_display": None,
        "max_salary_display": None,
    }
    
    if not div:
        print("No salary div found")
        return salary_data
    
    value_spans = div.find_all("span", class_="value")
    
    if len(value_spans) < 2:
        print(f"Expected 2 value spans, found {len(value_spans)}")
        return salary_data
    
    # Parse min salary (10% earn less than)
    min_span = value_spans[0]
    min_monthly_value = min_span.get("data-monthly-value", "")
    min_display = min_span.find("b").get_text(strip=True) if min_span.find("b") else ""
    
    # Parse max salary (10% earn more than)
    max_span = value_spans[1]
    max_monthly_value = max_span.get("data-monthly-value", "")
    max_display = max_span.find("b").get_text(strip=True) if max_span.find("b") else ""
    
    # Convert to integers
    try:
        salary_data["min_salary"] = int(float(min_monthly_value)) if min_monthly_value else None
        salary_data["min_salary_display"] = min_display
    except (ValueError, TypeError):
        print(f"Error converting min salary: {min_monthly_value}")
    
    try:
        salary_data["max_salary"] = int(float(max_monthly_value)) if max_monthly_value else None
        salary_data["max_salary_display"] = max_display
    except (ValueError, TypeError):
        print(f"Error converting max salary: {max_monthly_value}")
    
    return salary_data


def parse_job_salary(salary_text):
    """Parse salary range from text like '957,290 - 2,039,537 MNT'"""
    salary_parts = salary_text.split('-')
    
    if len(salary_parts) != 2:
        return 0, 0
    
    try:
        min_salary_str = salary_parts[0].strip().replace('MNT', '').replace(',', '')
        max_salary_str = salary_parts[1].strip().replace('MNT', '').replace(',', '')
        return int(min_salary_str), int(max_salary_str)
    except ValueError:
        return 0, 0


def extract_job_listings(content, url):
    """Extract job positions from the page"""
    job_list = []
    href_pattern = url.split('?')[0] + '/'
    
    for a_tag in content.find_all("a", href=True):
        job_link = str(a_tag["href"])
        
        # Skip non-job links
        if not job_link.startswith(href_pattern):
            continue
        
        job_data: dict[str, str | int] = {"job_url": job_link}
        
        # Extract job title
        title_div = a_tag.find("div", class_="col")
        if title_div:
            job_data["job_title"] = title_div.get_text(strip=True)
        
        # Extract salary range
        salary_span = a_tag.find("span", style="white-space: nowrap;")
        if salary_span:
            salary_text = salary_span.get_text(strip=True)
            min_salary, max_salary = parse_job_salary(salary_text)
            job_data["min_salary"] = min_salary
            job_data["max_salary"] = max_salary
        else:
            job_data["min_salary"] = 0
            job_data["max_salary"] = 0
        
        job_list.append(job_data)
    
    return job_list


def extract_jobs_from_html(content, url):
    """Extract salary range and job listings from HTML content"""
    result = extract_salary_range(content)
    result["job_list"] = extract_job_listings(content, url)
    return result


def fetch_page_with_playwright(url, name):
    """Fetch page using Playwright and save screenshot/HTML"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        
        # Save screenshot
        page.screenshot(path=f"images/paylab_{name}.png", full_page=True)
        
        # Parse and save HTML
        html_content = BeautifulSoup(page.content(), "html.parser")
        with open(f"htmls/paylab_{name}.html", "w", encoding="utf-8") as f:
            f.write(html_content.prettify())
        
        browser.close()
        
        return extract_jobs_from_html(html_content, url)


def load_job_urls(filepath):
    """Load job URLs from JSON file"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("job_urls", []), data


def save_results(filepath, data):
    """Save results to JSON file"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    # Load job URLs
    job_urls, existing_data = load_job_urls("data/paylab_job_urls.json")
    
    # Fetch data for each job URL
    jobs_data = []
    for job in job_urls:
        job_link = job.get("job_url", "")
        category_name = job.get("category_name", "")
        
        if not job_link:
            continue
        
        try:
            print(f"Fetching data for job URL: {job_link}")
            job_data = fetch_page_with_playwright(job_link, category_name)
            jobs_data.append(job_data)
        except Exception as e:
            print(f"Error fetching data for job URL {job_link}: {e}")
    
    # Prepare final result
    result = {
        "jobs_data": jobs_data,
        "min_salary": existing_data.get("min_salary", 0),
        "max_salary": existing_data.get("max_salary", 0),
    }
    
    # Save results
    save_results("results/paylab_job_data.json", result)
