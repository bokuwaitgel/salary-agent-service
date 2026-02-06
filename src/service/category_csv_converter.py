import json
import csv
from pathlib import Path

def flatten_job_category_data(data):
    """
    Flatten nested JSON structure to CSV-friendly format
    """
    flattened_data = []
    
    for category, category_data in data.items():
        category_count = category_data.get('count', 0)
        source_zangia_count = category_data.get('source_counts', {}).get('Zangia', 0)
        source_lambda_count = category_data.get('source_counts', {}).get('Lambda Global', 0)
        
        for job_entry in category_data.get('jobs', []):
            source = job_entry.get('source', '')
            job = job_entry.get('job', {})
            
            # Extract basic job info
            row = {
                'category': category,
                'category_count': category_count,
                'source_zangia_count': source_zangia_count,
                'source_lambda_count': source_lambda_count,
                'source': source,
                'job_name': job.get('name', ''),
                'company': job.get('company', ''),
                'min_salary': job.get('min_salary', ''),
                'max_salary': job.get('max_salary', ''),
                'bonus': job.get('bonus', ''),
                'job_level_category': job.get('job_level_category', ''),
                'job_grade': job.get('job_grade', ''),
                'job_level': job.get('job_level', ''),
                'job_category': job.get('job_category', ''),
            }
            
            # Flatten requirements into pipe-separated string
            requirements = job.get('requirements', [])
            if requirements:
                req_names = [req.get('name', '') or '' for req in requirements if req and isinstance(req, dict)]
                req_names = [name for name in req_names if name]  # Filter out empty strings
                row['requirements'] = ' | '.join(req_names)
            else:
                row['requirements'] = ''
            
            flattened_data.append(row)
    
    return flattened_data