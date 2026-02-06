import json
import asyncio
import pandas as pd
from pydantic_ai import BinaryContent
import os

from dotenv import load_dotenv
load_dotenv()

from schemas.techpack import TechpackJobSalaryCalculatorConfig, TechpackJobSalaryCalculatorAgent
from src.agent.agent import AgentProcessor
from src.service.paylab_data_converter import PaylabDataConverter
from src.service.csv_converter import flatten_job_data


merged_job_data_path = "results/merged_job_data.json"

def analyze_merged_job_data(input_path: str, output_path: str):
    """Analyze merged job data and save the analysis to output file."""

    with open(input_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)

    result = {}    

    for item in merged_data:
        job = item.get("job", {})
        job_level = job.get("job_level") or "Тодорхойгүй"
        print(f"Processing job level category: {job_level}")

        if job_level not in result:
            result[job_level] = {
                "count": 0,
                "source_counts": {},
                "jobs": []
            }
        if item["source"] not in result[job_level]["source_counts"]:
            result[job_level]["source_counts"][item["source"]] = 0
        result[job_level]["count"] += 1
        result[job_level]["source_counts"][item["source"]] += 1
        result[job_level]["jobs"].append(item)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


async def main():
    config = TechpackJobSalaryCalculatorConfig()
    agent = TechpackJobSalaryCalculatorAgent(config)
    processor = AgentProcessor(agent)
    

    level_data_path = "results/analyzed_job_data.json"
    with open(level_data_path, "r", encoding="utf-8") as f:
        level_data = json.load(f)
    
    statistic_data_path = "results/salary_statistics.json"
    with open(statistic_data_path, "r", encoding="utf-8") as f:
        statistic_data = json.load(f)
    
    paylab_salary_data_path = "results/paylab_job_data.json"
    with open(paylab_salary_data_path, "r", encoding="utf-8") as f:
        paylab_salary_data = json.load(f)

    #statistic csv file path
    statistic_data_csv_path = "temp/salary_statistics.csv"
    paylab_salary_data_csv_path = "temp/paylab_job_data.csv"
    os.makedirs("temp", exist_ok=True)
    #create statistic csv
    statistic_df = pd.DataFrame(statistic_data)
    statistic_df.to_csv(statistic_data_csv_path, index=False, encoding="utf-8-sig")
    #create paylab salary csv
    paylab = PaylabDataConverter(json_file_path=paylab_salary_data_path)
    paylab_data = paylab.load_json_data()
    paylab_df = paylab.convert_to_dataframe(paylab_data)
    paylab_df.to_csv(paylab_salary_data_csv_path, index=False, encoding="utf-8-sig")



    #ignore Tодорхойгүй level
    if "Тодорхойгүй" in level_data:
        del level_data["Тодорхойгүй"]

    
    level_results = {}

    for level, data in level_data.items():
        print(f"current level: {level}")

        
        jobs_in_level = data["jobs"]
        #flatten job data
        flatten_job = flatten_job_data(
            jobs_in_level
        )

        #save to a temporary file as csv
        temp_level_csv_path = f"temp/{level.replace('/', '_')}_job_data.csv"
        #to dataframe and save
        flatten_job_df = pd.DataFrame(flatten_job)
        flatten_job_df.to_csv(temp_level_csv_path, index=False, encoding="utf-8-sig")

    

        input = [
            BinaryContent(data=open(statistic_data_csv_path, "rb").read(), media_type="text/csv"),
            BinaryContent(data=open(paylab_salary_data_csv_path, "rb").read(), media_type="text/csv"),
            BinaryContent(data=open(temp_level_csv_path, "rb").read(), media_type="text/csv")
        ]

        

        response = await processor.calculate_salary(job_data=input)
        if response:
            if hasattr(response, 'model_dump'):
                level_results[level] = {
                    **response.model_dump(),
                    "job_count": data["count"],
                    "source_counts": data["source_counts"]
                }
            else:
                level_results[level] = response

    # Save level results to a file
    output_file = "outputs/job_level_salary_analysis_results.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(level_results, f, ensure_ascii=False, indent=2)

    
if __name__ == "__main__":
    # analyze_merged_job_data(merged_job_data_path, "results/analyzed_job_data.json")
    asyncio.run(main())