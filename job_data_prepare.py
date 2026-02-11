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

def main():
    repository: JobClassificationOutputRepository = dep
    datas = repository.get_all()
    print(f"Total classified jobs in database: {len(datas)}")

    config = SalaryAgentConfig()
    agent = SalaryAgent(config=config)
    processor = AgentProcessor(agent=agent)


    #prepare data for salary calculation
    function_map = {
    }
    industry_map = {
    }
    job_level_map = {
    }
    techpack_category_map = {
    }




    for data in datas:
        dict_data = data.__dict__
        
        # Parse JSON strings back to lists/dicts if they are strings
        if isinstance(dict_data.get('requirements'), str):
            dict_data['requirements'] = json.loads(dict_data['requirements'])
        if isinstance(dict_data.get('benefits'), str):
            dict_data['benefits'] = json.loads(dict_data['benefits'])
        if isinstance(dict_data.get('confidence_scores'), str):
            dict_data['confidence_scores'] = json.loads(dict_data['confidence_scores'])
        source = dict_data.get("source_job", "")
        classification_output = JobClassificationOutput(**dict_data)
        main_data = MainSalaryAgentData(
            title=classification_output.title,
            company_name=classification_output.company_name,
            job_function=classification_output.job_function,
            job_level=classification_output.job_level,
            experience_level=classification_output.experience_level,
            education_level=classification_output.education_level,
            salary_min=classification_output.salary_min,
            salary_max=classification_output.salary_max,
            requirements=classification_output.requirements,
            job_industry=classification_output.job_industry
        )

        # add to map
        #function_map[classification_output.job_function] = function_map.get(classification_output.job_function, 0) + 1
        if classification_output.job_function not in function_map:
            function_map[classification_output.job_function] = {
                "count": 0,
                "lambda": 0,
                "zangia": 0,
                "jobs": []
            }

        function_map[classification_output.job_function]["count"] += 1
        function_map[classification_output.job_function]["jobs"].append(main_data.model_dump())

        # industry_map[classification_output.job_industry] = industry_map.get(classification_output.job_industry, 0) + 1
        if classification_output.job_industry not in industry_map:
            industry_map[classification_output.job_industry] = {
                "count": 0,
                "lambda": 0,
                "zangia": 0,
                "jobs": []
            }
        industry_map[classification_output.job_industry]["count"] += 1
        industry_map[classification_output.job_industry]["jobs"].append(main_data.model_dump())

        # job_level_map[classification_output.job_level] = job_level_map.get(classification_output.job_level, 0) + 1
        if classification_output.job_level not in job_level_map:
            job_level_map[classification_output.job_level] = {
                "count": 0,
                "lambda": 0,
                "zangia": 0,
                "jobs": []
            }
        job_level_map[classification_output.job_level]["count"] += 1
        job_level_map[classification_output.job_level]["jobs"].append(main_data.model_dump())

        # techpack_category_map[classification_output.job_techpack_category] = techpack_category_map.get(classification_output.job_techpack_category, 0) + 1
        if classification_output.job_techpack_category not in techpack_category_map:
            techpack_category_map[classification_output.job_techpack_category] = {
                "count": 0,
                "lambda": 0,
                "zangia": 0,
                "jobs": []
            }
        techpack_category_map[classification_output.job_techpack_category]["count"] += 1
        techpack_category_map[classification_output.job_techpack_category]["jobs"].append(main_data.model_dump())

        #check source
        if source == "lambda":
            function_map[classification_output.job_function]["lambda"] += 1
            industry_map[classification_output.job_industry]["lambda"] += 1
            job_level_map[classification_output.job_level]["lambda"] += 1
            techpack_category_map[classification_output.job_techpack_category]["lambda"] += 1
        elif source == "zangia":
            function_map[classification_output.job_function]["zangia"] += 1
            industry_map[classification_output.job_industry]["zangia"] += 1
            job_level_map[classification_output.job_level]["zangia"] += 1
            techpack_category_map[classification_output.job_techpack_category]["zangia"] += 1

    #save maps to json file
    with open("results/function_map.json", "w", encoding="utf-8") as f:
        json.dump(function_map, f, ensure_ascii=False, indent=4)
    with open("results/industry_map.json", "w", encoding="utf-8") as f:
        json.dump(industry_map, f, ensure_ascii=False, indent=4)
    with open("results/job_level_map.json", "w", encoding="utf-8") as f:
        json.dump(job_level_map, f, ensure_ascii=False, indent=4)
    with open("results/techpack_category_map.json", "w", encoding="utf-8") as f:
        json.dump(techpack_category_map, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()