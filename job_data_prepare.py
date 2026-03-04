from schemas.database.base_classifier_db import JobClassificationOutputTable
from src.dependencies import get_classifier_output_repository
from src.repositories.database import JobClassificationOutputRepository

from schemas.salary_agent import SalaryAgentOutput, SalaryAgent, SalaryAgentConfig, SalaryAgentInput, MainSalaryAgentData
from schemas.base_classifier import JobClassificationOutput
from src.agent.agent import AgentProcessor

import asyncio
import json
from dotenv import load_dotenv
import os
from markdownify import markdownify as md

dep = get_classifier_output_repository()

current_year = "2026"
current_month = "02"

def main():
    repository: JobClassificationOutputRepository = dep
    datas = repository.get_by_query(
        (JobClassificationOutputTable.year == current_year) & (JobClassificationOutputTable.month == current_month)
    )
    print(f"Total classified jobs in database: {len(datas)}")

    # config = SalaryAgentConfig()
    # agent = SalaryAgent(config=config)
    # processor = AgentProcessor(agent=agent)

    # industry_set = set()
    # job_function_set = set()
    # job_level_set = set()
    # for data in datas:
    map_prepared_data = {}
    for data in datas:
        dict_data = data.__dict__
        industry = dict_data.get("job_industry", "")
        job_function = dict_data.get("job_function", "")
        job_level = dict_data.get("job_level", "")
        techpack_category = dict_data.get("job_techpack_category", "")

        if industry not in map_prepared_data:
            map_prepared_data[industry] = {}
        if job_function not in map_prepared_data[industry]:
            map_prepared_data[industry][job_function] = {}

        if job_level not in map_prepared_data[industry][job_function]:
            map_prepared_data[industry][job_function][job_level] = {}
        
        if techpack_category not in map_prepared_data[industry][job_function][job_level]:
            map_prepared_data[industry][job_function][job_level][techpack_category] = {
                "count": 0,
                "zangia_count": 0,
                "lambda_count": 0,
                "salaries": []
            }
        map_prepared_data[industry][job_function][job_level][techpack_category]["count"] += 1
        if dict_data.get("source_job") == "zangia":
            map_prepared_data[industry][job_function][job_level][techpack_category]["zangia_count"] += 1
        elif dict_data.get("source_job") == "lambda":
            map_prepared_data[industry][job_function][job_level][techpack_category]["lambda_count"] += 1

        #prepare salary data for calculation, only add if salary is not None and greater than 0
        data_salary = {
            "title": dict_data.get("title", ""),
            "company_name": dict_data.get("company_name", ""),
            "experience_level": dict_data.get("experience_level", ""),
            "education_level": dict_data.get("education_level", ""),
            "salary_min": dict_data.get("salary_min"),
            "salary_max": dict_data.get("salary_max"),
            "year": dict_data.get("year", ""),
            "month": dict_data.get("month", ""),
            "source": dict_data.get("source_job", ""),
        }

        map_prepared_data[industry][job_function][job_level][techpack_category]["salaries"].append(data_salary)

    #save prepared data into json file
    with open(f"results/prepared_salary_data_{current_year}_{current_month}.json", "w", encoding="utf-8") as f:
        json.dump(map_prepared_data, f, ensure_ascii=False, indent=4)

    

if __name__ == "__main__":
    main()