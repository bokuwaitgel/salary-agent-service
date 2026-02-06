import json

zangia_job_data_path = "results/zangia_job_classification_results.json"
lambda_job_data_path = "results/lambda_job_classification_results.json"

def merge_job_data(zangia_path: str, lambda_path: str, output_path: str):
    """Merge job data from Zangia and Lambda Global and save to output file."""

    list_of_jobs = []

    with open(zangia_path, "r", encoding="utf-8") as f:
        zangia_data = json.load(f)
    
    with open(lambda_path, "r", encoding="utf-8") as f:
        lambda_data = json.load(f)
    
    for zangia in zangia_data:
        list_of_jobs.append({
            "source": "Zangia",
            "job": zangia
        })
    for lambda_job in lambda_data:
        list_of_jobs.append({
            "source": "Lambda Global",
            "job": lambda_job
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(list_of_jobs, f, ensure_ascii=False, indent=2)
if __name__ == "__main__":
    merge_job_data(zangia_job_data_path, lambda_job_data_path, "results/merged_job_data.json")
