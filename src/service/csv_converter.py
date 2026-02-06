import json
import csv
from pathlib import Path

def flatten_job_data(data):
    """
    Flatten nested JSON structure to CSV-friendly format
    """
    flattened_data = []
    
    for entry in data:
        source = entry.get('source', '')
        job = entry.get('job', {})
        
        # Extract basic job info
        row = {
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
        
        # Flatten requirements into comma-separated string
        requirements = job.get('requirements', [])
        if requirements:
            req_names = [req.get('name', '') or '' for req in requirements if req and isinstance(req, dict)]
            req_names = [name for name in req_names if name]  # Filter out empty strings
            row['requirements'] = ' | '.join(req_names)
        else:
            row['requirements'] = ''
        
        flattened_data.append(row)
    
    return flattened_data

def main():
    # Read JSON file
    input_file = Path('results/merged_job_data.json')
    output_file = Path('results/merged_job_data.csv')
    
    print(f"Reading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total entries: {len(data)}")
    
    # Flatten data
    print("Flattening data structure...")
    flattened_data = flatten_job_data(data)
    
    # Write to CSV
    print(f"Writing to {output_file}...")
    fieldnames = [
        'source', 'job_name', 'company', 'min_salary', 'max_salary', 
        'bonus', 'job_level_category', 'job_grade', 'job_level', 
        'job_category', 'requirements'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)
    
    print(f"✓ Successfully converted {len(flattened_data)} entries to CSV")
    print(f"✓ Saved to: {output_file}")
    
    # Print sample statistics
    sources = {}
    for entry in flattened_data:
        source = entry['source']
        sources[source] = sources.get(source, 0) + 1
    
    print("\nData breakdown by source:")
    for source, count in sources.items():
        print(f"  - {source}: {count} jobs")

if __name__ == '__main__':
    main()
