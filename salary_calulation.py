from src.dependencies import get_salary_calculation_output_repository, get_classifier_output_repository
from src.repositories.database import SalaryCalculationOutputRepository, JobClassificationOutputTable
from schemas.salary_agent import SalaryAgentOutput, SalaryAgent, SalaryAgentConfig, SalaryAgentInput, MainSalaryAgentData, JobXEducationLevel 
from schemas.base_classifier import JobClassificationOutput
from src.agent.agent import AgentProcessor
from src.service.paylab_data_converter import PaylabDataConverter

from pydantic_ai import BinaryContent
from typing import List
import asyncio
import sys
import json
from dotenv import load_dotenv
import os
from markdownify import markdownify as md
import pandas as pd
load_dotenv()

# Fix for Windows asyncio event loop issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

function_data_path = "results/function_map.json"
industry_data_path = "results/industry_map.json"
job_level_data_path = "results/job_level_map.json"
techpack_category_data_path = "results/techpack_category_map.json"

#addictional data for salary calculation, we can use this data to analyze salary 
paylab_data_path = "additional_data/paylab_job_data.json"
statista_data_path = "additional_data/salary_statistics.json"

current_year = 2026
current_month = 3

config = SalaryAgentConfig()
agent = SalaryAgent(config=config)
processor = AgentProcessor(agent=agent)

#prapare additional data json into csv
#paylab data is in json format, we need to convert it into csv format for easier analysis and use in salary calculation agent
paylab_converter = PaylabDataConverter(paylab_data_path)
paylab_converter.convert_and_save(output_dir="additional_data/paylab_csv")

#statistic data into csv
statistic_df = pd.read_json(statista_data_path)

#before save value * 1000
statistic_df["value"] = statistic_df["value"] * 1000
statistic_df.to_csv("additional_data/salary_statistics.csv", index=False)

#load additional data
additional_data = {
    "paylab": BinaryContent(data=open("additional_data/paylab_csv/paylab_all_jobs.csv", "rb").read(), media_type="text/csv"),
    "salary_statistics": BinaryContent(data=open("additional_data/salary_statistics.csv", "rb").read(), media_type="text/csv"),
}

repository: SalaryCalculationOutputRepository = get_salary_calculation_output_repository()
classifier_repository = get_classifier_output_repository()
_group_maps_cache = None


def _load_group_maps_from_db():
    datas = classifier_repository.get_by_query(
        (JobClassificationOutputTable.year == str(current_year)) & (JobClassificationOutputTable.month == f"{current_month:02d}")
    )
    print(f"Total classified jobs in database: {len(datas)}")

    function_map = {}
    industry_map = {}
    job_level_map = {}
    techpack_category_map = {}

    def _update_bucket(target_map, category, job_payload, source_name):
        if not category:
            return
        if category not in target_map:
            target_map[category] = {
                "count": 0,
                "lambda": 0,
                "zangia": 0,
                "jobs": []
            }
        target_map[category]["count"] += 1
        target_map[category]["jobs"].append(job_payload)

        if source_name == "lambda":
            target_map[category]["lambda"] += 1
        elif source_name == "zangia":
            target_map[category]["zangia"] += 1

    for data in datas:
        dict_data = data.__dict__.copy()
        source = str(dict_data.get("source_job", "")).strip().lower()

        requirements = dict_data.get("requirements")
        if isinstance(requirements, str):
            try:
                requirements = json.loads(requirements)
            except json.JSONDecodeError:
                requirements = []

        main_data = MainSalaryAgentData(
            title=dict_data.get("title", ""),
            company_name=dict_data.get("company_name"),
            job_function=dict_data.get("job_function"),
            job_level=dict_data.get("job_level"),
            experience_level=dict_data.get("experience_level"),
            education_level=dict_data.get("education_level"),
            salary_min=dict_data.get("salary_min"),
            salary_max=dict_data.get("salary_max"),
            requirements=requirements if isinstance(requirements, list) else [],
            job_industry=dict_data.get("job_industry")
        )
        job_payload = main_data.model_dump()

        _update_bucket(function_map, dict_data.get("job_function"), job_payload, source)
        _update_bucket(industry_map, dict_data.get("job_industry"), job_payload, source)
        _update_bucket(job_level_map, dict_data.get("job_level"), job_payload, source)
        _update_bucket(techpack_category_map, dict_data.get("job_techpack_category"), job_payload, source)

    return {
        "function": function_map,
        "industry": industry_map,
        "job_level": job_level_map,
        "techpack_category": techpack_category_map,
    }


def _get_group_maps_from_db():
    global _group_maps_cache
    if _group_maps_cache is None:
        _group_maps_cache = _load_group_maps_from_db()
    return _group_maps_cache


async def industry_salary():
    industry_map = _get_group_maps_from_db().get("industry", {})
    #load SalaryAgentInput
    for industry, details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        jobs = details.get("jobs", [])
        job_inputs = []
        for job in jobs:
            job_input = MainSalaryAgentData(**job)
            job_inputs.append(job_input)
        salary_input = SalaryAgentInput(
            title=industry,
            main_data=job_inputs,
            additional_data=additional_data
        )

        result = await processor.calculate_salary(job_data=salary_input)
        print(f"Salary analysis for industry: {industry}")
        print(result)
        print("----")

        if result:
            experience_salary_breakdown = "["
            experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
            for item in experience_salary_breakdown_list:
                education_level = item.experience_level
                min_salary = item.salary_min
                max_salary = item.salary_max
                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                #dump experience salary breakdown into json string
                experience_salary_breakdown += json.dumps({
                    "education_level": education_level,
                    "min_salary": min_salary,
                    "max_salary": max_salary
                }, ensure_ascii=False) + ","

            experience_salary_breakdown += "]"

            data_output = {
                "title": industry,
                "reasoning": result.reasoning, 
                "min_salary": result.min_salary,
                "max_salary": result.max_salary,
                "average_salary": result.average_salary,
                "job_count": details.get("count", 0),
                "zangia_count": details.get("zangia", 0),
                "lambda_count": details.get("lambda", 0),
                "experience_salary_breakdown": experience_salary_breakdown,
                "industry": industry,
                "job_function": "all",
                "job_level": "all",
                "techpack_category": "all",
                "type": "industry",
                "year": current_year,
                "month": current_month,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for industry: {industry}")

async def functional_salary():
    function_map = _get_group_maps_from_db().get("function", {})
    #load SalaryAgentInput
    for function, details in function_map.items():
        #ignore Бусад
        if function == "Бусад":
            continue

        jobs = details.get("jobs", [])
        job_inputs = []
        for job in jobs:
            job_input = MainSalaryAgentData(**job)
            job_inputs.append(job_input)


        
        salary_input = SalaryAgentInput(
            title=function,
            main_data=job_inputs,
            additional_data=additional_data
        )

        result = await processor.calculate_salary(job_data=salary_input)
        print(f"Salary analysis for function: {function}")
        print(result)
        print("----")

        if result:
       
            experience_salary_breakdown = "["
            experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
            for item in experience_salary_breakdown_list:
                education_level = item.experience_level
                min_salary = item.salary_min
                max_salary = item.salary_max
                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                #dump experience salary breakdown into json string
                experience_salary_breakdown += json.dumps({
                    "education_level": education_level,
                    "min_salary": min_salary,
                    "max_salary": max_salary
                }, ensure_ascii=False) + ","

            experience_salary_breakdown += "]"

            data_output = {
                "title": function,
                "reasoning": result.reasoning, 
                "min_salary": result.min_salary,
                "max_salary": result.max_salary,
                "average_salary": result.average_salary,
                "job_count": details.get("count", 0),
                "experience_salary_breakdown": experience_salary_breakdown,
                "industry": "all",
                "job_function": function,
                "job_level": "all",
                "techpack_category": "all",
                "zangia_count": details.get("zangia", 0),
                "lambda_count": details.get("lambda", 0),
                "type": "function",
                "year": current_year,
                "month": current_month,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for function: {function}")
    
    # get all industry data for all function salary analysis
    industry_map = _get_group_maps_from_db().get("industry", {})
    # industry -> function -> datas map for analysis of function salary by industry
    for industry, details in industry_map.items():
        if industry == "Бусад":
            continue
        jobs = details.get("jobs", [])
        industry_function_map = {}
        for job in jobs:
            job_function = job.get("job_function", "Бусад")
            if job_function not in industry_function_map:
                industry_function_map[job_function] = []
            industry_function_map[job_function].append(job)
        
        for function, function_jobs in industry_function_map.items():
            if function == "Бусад":
                continue
            job_inputs = []
            for job in function_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{industry} - {function}",
                main_data=job_inputs,
                additional_data=additional_data
            )

            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for industry: {industry}, function: {function}")
            print(result)
            print("----")

            if result:
                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"

                data_output = {
                    "title": f"{industry} - {function}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(function_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": industry,
                    "job_function": function,
                    "job_level": "all",
                    "techpack_category": "all",
                    "zangia_count": len([job for job in function_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in function_jobs if job.get("source_job") == "lambda"]),
                    "type": "function_by_industry",
                    "year": 2025,
                    "month": 2,
                }

                repository.create(data_output)
                print(f"Saved salary analysis for industry: {industry}, function: {function}")

            
    

async def job_level_salary():
    job_level_map = _get_group_maps_from_db().get("job_level", {})
    #load SalaryAgentInput
    for job_level, details in job_level_map.items():
        #ignore Бусад
        if job_level == "Бусад":
            continue

        jobs = details.get("jobs", [])
        job_inputs = []
        for job in jobs:
            job_input = MainSalaryAgentData(**job)
            job_inputs.append(job_input)


        
        salary_input = SalaryAgentInput(
            title=job_level,
            main_data=job_inputs,
            additional_data=additional_data
        )

        result = await processor.calculate_salary(job_data=salary_input)
        print(f"Salary analysis for job level: {job_level}")
        print(result)
        print("----")

        if result:
            experience_salary_breakdown = "["
            experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
            for item in experience_salary_breakdown_list:
                education_level = item.experience_level
                min_salary = item.salary_min
                max_salary = item.salary_max
                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                #dump experience salary breakdown into json string
                experience_salary_breakdown += json.dumps({
                    "education_level": education_level,
                    "min_salary": min_salary,
                    "max_salary": max_salary
                }, ensure_ascii=False) + ","

            experience_salary_breakdown += "]"

            data_output = {
                "title": job_level,
                "reasoning": result.reasoning, 
                "min_salary": result.min_salary,
                "max_salary": result.max_salary,
                "average_salary": result.average_salary,
                "job_count": details.get("count", 0),
                "zangia_count": details.get("zangia", 0),
                "lambda_count": details.get("lambda", 0),
                "experience_salary_breakdown": experience_salary_breakdown,
                "type": "job_level",
                "industry": "all",
                "job_function": "all",
                "job_level": job_level,
                "techpack_category": "all",
                "year": current_year,
                "month": current_month,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for job level: {job_level}")

    # get all industry data for all job level salary analysis
    industry_map = _get_group_maps_from_db().get("industry", {})
    # industry -> job level -> datas map for analysis of job level salary by industry
    for industry, details in industry_map.items():
        if industry == "Бусад":
            continue
        jobs = details.get("jobs", [])
        industry_job_level_map = {}
        for job in jobs:
            job_level = job.get("job_level", "Бусад")
            if job_level not in industry_job_level_map:
                industry_job_level_map[job_level] = []
            industry_job_level_map[job_level].append(job)
        
        for job_level, job_level_jobs in industry_job_level_map.items():
            if job_level == "Бусад":
                continue
            job_inputs = []
            for job in job_level_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{industry} - {job_level}",
                main_data=job_inputs,
                additional_data=additional_data
            )

            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for industry: {industry}, job level: {job_level}")
            print(result)
            print("----")

            if result:
                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"

                data_output = {
                    "title": f"{industry} - {job_level}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(job_level_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": industry,
                    "job_function": "all",
                    "job_level": job_level,
                    "techpack_category": "all",
                    "zangia_count": len([job for job in job_level_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in job_level_jobs if job.get("source_job") == "lambda"]),
                    "type": "job_level_by_industry",
                    "year": current_year,
                    "month": current_month,
                }
                repository.create(data_output)
                print(f"Saved salary analysis for industry: {industry}, job level: {job_level}")
        
    # get all function data for all job level salary analysis
    function_map = _get_group_maps_from_db().get("function", {})
    # function -> job level -> datas map for analysis of job level salary by function
    for function, details in function_map.items():
        if function == "Бусад":
            continue
        jobs = details.get("jobs", [])
        function_job_level_map = {}
        for job in jobs:
            job_level = job.get("job_level", "Бусад")
            if job_level not in function_job_level_map:
                function_job_level_map[job_level] = []
            function_job_level_map[job_level].append(job)
        
        for job_level, job_level_jobs in function_job_level_map.items():
            if job_level == "Бусад":
                continue
            job_inputs = []
            for job in job_level_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{function} - {job_level}",
                main_data=job_inputs,
                additional_data=additional_data
            )

            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for function: {function}, job level: {job_level}")
            print(result)
            print("----")

            if result:
                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"

                data_output = {
                    "title": f"{function} - {job_level}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(job_level_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": "all",
                    "job_function": function,
                    "job_level": job_level,
                    "techpack_category": "all",
                    "zangia_count": len([job for job in job_level_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in job_level_jobs if job.get("source_job") == "lambda"]),
                    "type": "job_level_by_function",
                    "year": current_year,
                    "month": current_month,
                }
                repository.create(data_output)
                print(f"Saved salary analysis for function: {function}, job level: {job_level}")

    # industry + function + job level combination salary analysis
    for industry, industry_details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        industry_jobs = industry_details.get("jobs", [])
        industry_function_map = {}
        for job in industry_jobs:
            job_function = job.get("job_function", "Бусад")
            if job_function not in industry_function_map:
                industry_function_map[job_function] = []
            industry_function_map[job_function].append(job)
        for function, function_jobs in industry_function_map.items():
            #ignore Бусад
            if function == "Бусад":
                continue
            function_job_level_map = {}
            for job in function_jobs:
                job_level = job.get("job_level", "Бусад")
                if job_level not in function_job_level_map:
                    function_job_level_map[job_level] = []
                function_job_level_map[job_level].append(job)

                for job_level, job_level_jobs in function_job_level_map.items():
                    #ignore Бусад
                    if job_level == "Бусад":
                        continue
                    job_inputs = []
                    for job in job_level_jobs:
                        job_input = MainSalaryAgentData(**job)
                        job_inputs.append(job_input)

                    salary_input = SalaryAgentInput(
                        title=f"{industry} - {function} - {job_level}",
                        main_data=job_inputs,

                        additional_data=additional_data
                    )
                    result = await processor.calculate_salary(job_data=salary_input)
                    print(f"Salary analysis for industry: {industry}, function: {function}, job level: {job_level}")
                    print(result)
                    print("----")
                    if result:

                        experience_salary_breakdown = "["
                        experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                        for item in experience_salary_breakdown_list:
                            education_level = item.experience_level
                            min_salary = item.salary_min
                            max_salary = item.salary_max
                            print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                            #dump experience salary breakdown into json string
                            experience_salary_breakdown += json.dumps({
                                "education_level": education_level,
                                "min_salary": min_salary,
                                "max_salary": max_salary
                            }, ensure_ascii=False) + ","

                        experience_salary_breakdown += "]"
                        data_output = {
                            "title": f"{industry} - {function} - {job_level}",
                            "reasoning": result.reasoning, 
                            "min_salary": result.min_salary,
                            "max_salary": result.max_salary,
                            "average_salary": result.average_salary,
                            "job_count": len(job_level_jobs),
                            "experience_salary_breakdown": experience_salary_breakdown,
                            "industry": industry,
                            "job_function": function,
                            "job_level": job_level,
                            "techpack_category": "all",
                            "zangia_count": len([job for job in job_level_jobs if job.get("source_job") == "zangia"]),
                            "lambda_count": len([job for job in job_level_jobs if job.get("source_job") == "lambda"]),
                            "type": "job_level_by_industry_function",
                            "year": current_year,
                            "month": current_month,
                        }
                        repository.create(data_output)
                        print(f"Saved salary analysis for industry: {industry}, function: {function}, job level: {job_level}")

        

async def techpack_category_salary():
    techpack_category_map = _get_group_maps_from_db().get("techpack_category", {})
    #load SalaryAgentInput
    for techpack_category, details in techpack_category_map.items():
        #ignore Бусад
        if techpack_category == "Бусад":
            continue

        jobs = details.get("jobs", [])
        job_inputs = []
        for job in jobs:
            job_input = MainSalaryAgentData(**job)
            job_inputs.append(job_input)


        
        salary_input = SalaryAgentInput(
            title=techpack_category,
            main_data=job_inputs,
            additional_data=additional_data
        )

        result = await processor.calculate_salary(job_data=salary_input)
        print(f"Salary analysis for techpack category: {techpack_category}")
        print(result)
        print("----")

        if result:
            experience_salary_breakdown = "["
            experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
            for item in experience_salary_breakdown_list:
                education_level = item.experience_level
                min_salary = item.salary_min
                max_salary = item.salary_max
                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                #dump experience salary breakdown into json string
                experience_salary_breakdown += json.dumps({
                    "education_level": education_level,
                    "min_salary": min_salary,
                    "max_salary": max_salary
                }, ensure_ascii=False) + ","

            experience_salary_breakdown += "]"
            data_output = {
                "title": techpack_category,
                "reasoning": result.reasoning, 
                "min_salary": result.min_salary,
                "max_salary": result.max_salary,
                "average_salary": result.average_salary,
                "job_count": details.get("count", 0),
                "zangia_count": details.get("zangia", 0),
                "lambda_count": details.get("lambda", 0),
                "experience_salary_breakdown": experience_salary_breakdown,
                "type": "techpack_category",
                "industry": "all",
                "job_function": "all",
                "job_level": "all",
                "techpack_category": techpack_category,
                "year": current_year,
                "month": current_month,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for techpack category: {techpack_category}")
        

    # industry + techpack category combination salary analysis
    industry_map = _get_group_maps_from_db().get("industry", {})
    # industry -> techpack category -> datas map for analysis of techpack category salary by industry
    for industry, industry_details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        industry_jobs = industry_details.get("jobs", [])
        industry_techpack_category_map = {}
        for job in industry_jobs:
            job_techpack_category = job.get("job_techpack_category", "Бусад")
            if job_techpack_category not in industry_techpack_category_map:
                industry_techpack_category_map[job_techpack_category] = []
            industry_techpack_category_map[job_techpack_category].append(job)
        for techpack_category, techpack_category_jobs in industry_techpack_category_map.items():
            #ignore Бусад
            if techpack_category == "Бусад":
                continue
            job_inputs = []
            for job in techpack_category_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{industry} - {techpack_category}",
                main_data=job_inputs,
                additional_data=additional_data
            )
            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for industry: {industry}, techpack category: {techpack_category}")
            print(result)
            print("----")
            if result:

                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"
                data_output = {
                    "title": f"{industry} - {techpack_category}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(techpack_category_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": industry,
                    "job_function": "all",
                    "job_level": "all",
                    "techpack_category": techpack_category,
                    "zangia_count": len([job for job in techpack_category_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in techpack_category_jobs if job.get("source_job") == "lambda"]),
                    "type": "techpack_category_by_industry",
                    "year": current_year,
                    "month": current_month,
                }
                repository.create(data_output)
                print(f"Saved salary analysis for industry: {industry}, techpack category: {techpack_category}")

    # function + techpack category combination salary analysis
    function_map = _get_group_maps_from_db().get("function", {})
    # function -> techpack category -> datas map for analysis of techpack category salary by function
    for function, function_details in function_map.items():
        #ignore Бусад
        if function == "Бусад":
            continue

        function_jobs = function_details.get("jobs", [])
        function_techpack_category_map = {}
        for job in function_jobs:
            job_techpack_category = job.get("job_techpack_category", "Бусад")
            if job_techpack_category not in function_techpack_category_map:
                function_techpack_category_map[job_techpack_category] = []
            function_techpack_category_map[job_techpack_category].append(job)
        for techpack_category, techpack_category_jobs in function_techpack_category_map.items():
            #ignore Бусад
            if techpack_category == "Бусад":
                continue
            job_inputs = []
            for job in techpack_category_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{function} - {techpack_category}",
                main_data=job_inputs,
                additional_data=additional_data
            )
            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for function: {function}, techpack category: {techpack_category}")
            print(result)
            print("----")
            if result:

                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"
                data_output = {
                    "title": f"{function} - {techpack_category}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(techpack_category_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": "all",
                    "job_function": function,
                    "job_level": "all",
                    "techpack_category": techpack_category,
                    "zangia_count": len([job for job in techpack_category_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in techpack_category_jobs if job.get("source_job") == "lambda"]),
                    "type": "techpack_category_by_function",
                    "year": current_year,
                    "month": current_month,
                }
                repository.create(data_output)
                print(f"Saved salary analysis for function: {function}, techpack category: {techpack_category}")

    # level + techpack category combination salary analysis
    job_level_map = _get_group_maps_from_db().get("job_level", {})
    # job level -> techpack category -> datas map for analysis of techpack category salary by job level
    for job_level, job_level_details in job_level_map.items():
        #ignore Бусад
        if job_level == "Бусад":
            continue

        job_level_jobs = job_level_details.get("jobs", [])
        job_level_techpack_category_map = {}
        for job in job_level_jobs:
            job_techpack_category = job.get("job_techpack_category", "Бусад")
            if job_techpack_category not in job_level_techpack_category_map:
                job_level_techpack_category_map[job_techpack_category] = []
            job_level_techpack_category_map[job_techpack_category].append(job)
        for techpack_category, techpack_category_jobs in job_level_techpack_category_map.items():
            #ignore Бусад
            if techpack_category == "Бусад":
                continue
            job_inputs = []
            for job in techpack_category_jobs:
                job_input = MainSalaryAgentData(**job)
                job_inputs.append(job_input)

            salary_input = SalaryAgentInput(
                title=f"{job_level} - {techpack_category}",
                main_data=job_inputs,
                additional_data=additional_data
            )
            result = await processor.calculate_salary(job_data=salary_input)
            print(f"Salary analysis for job level: {job_level}, techpack category: {techpack_category}")
            print(result)
            print("----")
            if result:

                experience_salary_breakdown = "["
                experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                for item in experience_salary_breakdown_list:
                    education_level = item.experience_level
                    min_salary = item.salary_min
                    max_salary = item.salary_max
                    print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                    #dump experience salary breakdown into json string
                    experience_salary_breakdown += json.dumps({
                        "education_level": education_level,
                        "min_salary": min_salary,
                        "max_salary": max_salary
                    }, ensure_ascii=False) + ","

                experience_salary_breakdown += "]"
                data_output = {
                    "title": f"{job_level} - {techpack_category}",
                    "reasoning": result.reasoning, 
                    "min_salary": result.min_salary,
                    "max_salary": result.max_salary,
                    "average_salary": result.average_salary,
                    "job_count": len(techpack_category_jobs),
                    "experience_salary_breakdown": experience_salary_breakdown,
                    "industry": "all",
                    "job_function": "all",
                    "job_level": job_level,
                    "techpack_category": techpack_category,
                    "zangia_count": len([job for job in techpack_category_jobs if job.get("source_job") == "zangia"]),
                    "lambda_count": len([job for job in techpack_category_jobs if job.get("source_job") == "lambda"]),
                    "type": "techpack_category_by_job_level",
                    "year": current_year,
                    "month": current_month,
                }

                repository.create(data_output)
                print(f"Saved salary analysis for job level: {job_level}, techpack category: {techpack_category}")

    # industry + function + job level + techpack category combination salary analysis
    for industry, industry_details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        industry_jobs = industry_details.get("jobs", [])
        industry_function_map = {}
        for job in industry_jobs:
            job_function = job.get("job_function", "Бусад")
            if job_function not in industry_function_map:
                industry_function_map[job_function] = []
            industry_function_map[job_function].append(job)
        for function, function_jobs in industry_function_map.items():
            #ignore Бусад
            if function == "Бусад":
                continue
            function_job_level_map = {}
            for job in function_jobs:
                job_level = job.get("job_level", "Бусад")
                if job_level not in function_job_level_map:
                    function_job_level_map[job_level] = []
                function_job_level_map[job_level].append(job)

                for job_level, job_level_jobs in function_job_level_map.items():
                    #ignore Бусад
                    if job_level == "Бусад":
                        continue
                    job_techpack_category_map = {}
                    for job in job_level_jobs:
                        job_techpack_category = job.get("job_techpack_category", "Бусад")
                        if job_techpack_category not in job_techpack_category_map:
                            job_techpack_category_map[job_techpack_category] = []
                        job_techpack_category_map[job_techpack_category].append(job)

                    for techpack_category, techpack_category_jobs in job_techpack_category_map.items():
                        #ignore Бусад
                        if techpack_category == "Бусад":
                            continue
                        job_inputs = []
                        for job in techpack_category_jobs:
                            job_input = MainSalaryAgentData(**job)
                            job_inputs.append(job_input)

                        salary_input = SalaryAgentInput(
                            title=f"{industry} - {function} - {job_level} - {techpack_category}",
                            main_data=job_inputs,
                            additional_data=additional_data
                        )
                        result = await processor.calculate_salary(job_data=salary_input)
                        print(f"Salary analysis for industry: {industry}, function: {function}, job level: {job_level}, techpack category: {techpack_category}")
                        print(result)
                        print("----")
                        if result:

                            experience_salary_breakdown = "["
                            experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                            for item in experience_salary_breakdown_list:
                                education_level = item.experience_level
                                min_salary = item.salary_min
                                max_salary = item.salary_max
                                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                                #dump experience salary breakdown into json string
                                experience_salary_breakdown += json.dumps({
                                    "education_level": education_level,
                                    "min_salary": min_salary,
                                    "max_salary": max_salary
                                }, ensure_ascii=False) + ","
                            experience_salary_breakdown += "]"
                            data_output = {
                                "title": f"{industry} - {function} - {job_level} - {techpack_category} Salary Analysis",
                                "reasoning": result.reasoning,
                                "min_salary": result.min_salary,
                                "max_salary": result.max_salary,
                                "average_salary": result.average_salary,
                                "job_count": len(techpack_category_jobs),
                                "experience_salary_breakdown": experience_salary_breakdown,
                                "type": "detailed",
                                "industry": industry,
                                "job_function": function,
                                "job_level": job_level,
                                "techpack_category": techpack_category,
                                "year": current_year,
                                "month": current_month,
                            }
                            repository.create(data_output)
                            print(f"Saved salary analysis for {industry} - {function} - {job_level} - {techpack_category}")

    # industry + function + techpack category combination salary analysis
    for industry, industry_details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        industry_jobs = industry_details.get("jobs", [])
        industry_function_map = {}
        for job in industry_jobs:
            job_function = job.get("job_function", "Бусад")
            if job_function not in industry_function_map:
                industry_function_map[job_function] = []
            industry_function_map[job_function].append(job)
        for function, function_jobs in industry_function_map.items():
            #ignore Бусад
            if function == "Бусад":
                continue
            function_techpack_category_map = {}
            for job in function_jobs:
                job_techpack_category = job.get("job_techpack_category", "Бусад")
                if job_techpack_category not in function_techpack_category_map:
                    function_techpack_category_map[job_techpack_category] = []
                function_techpack_category_map[job_techpack_category].append(job)

            for techpack_category, techpack_category_jobs in function_techpack_category_map.items():
                #ignore Бусад
                if techpack_category == "Бусад":
                    continue
                job_inputs = []
                for job in techpack_category_jobs:
                    job_input = MainSalaryAgentData(**job)
                    job_inputs.append(job_input)

                salary_input = SalaryAgentInput(
                    title=f"{industry} - {function} - {techpack_category}",
                    main_data=job_inputs,
                    additional_data=additional_data
                )
                result = await processor.calculate_salary(job_data=salary_input)
                print(f"Salary analysis for industry: {industry}, function: {function}, techpack category: {techpack_category}")
                print(result)
                print("----")
                if result:

                    experience_salary_breakdown = "["
                    experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                    for item in experience_salary_breakdown_list:
                        education_level = item.experience_level
                        min_salary = item.salary_min
                        max_salary = item.salary_max
                        print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                        #dump experience salary breakdown into json string
                        experience_salary_breakdown += json.dumps({
                            "education_level": education_level,
                            "min_salary": min_salary,
                            "max_salary": max_salary
                        }, ensure_ascii=False) + ","
                    experience_salary_breakdown += "]"
                    data_output = {
                        "title": f"{industry} - {function} - {techpack_category} Salary Analysis",
                        "reasoning": result.reasoning,
                        "min_salary": result.min_salary,
                        "max_salary": result.max_salary,
                        "average_salary": result.average_salary,
                        "job_count": len(techpack_category_jobs),
                        "experience_salary_breakdown": experience_salary_breakdown,
                        "type": "industry_function_techpack_category",
                        "industry": industry,
                        "job_function": function,
                        "job_level": "all",
                        "techpack_category": techpack_category,
                        "year": current_year,
                        "month": current_month,
                    }
                    repository.create(data_output)
                    print(f"Saved salary analysis for industry: {industry}, function: {function}, techpack category: {techpack_category}")
    #industry + job level + techpack category combination salary analysis
    for industry, industry_details in industry_map.items():
        #ignore Бусад
        if industry == "Бусад":
            continue

        industry_jobs = industry_details.get("jobs", [])
        industry_job_level_map = {}
        for job in industry_jobs:
            job_level = job.get("job_level", "Бусад")
            if job_level not in industry_job_level_map:
                industry_job_level_map[job_level] = []
            industry_job_level_map[job_level].append(job)
        for job_level, job_level_jobs in industry_job_level_map.items():
            #ignore Бусад
            if job_level == "Бусад":
                continue
            job_level_techpack_category_map = {}
            for job in job_level_jobs:
                job_techpack_category = job.get("job_techpack_category", "Бусад")
                if job_techpack_category not in job_level_techpack_category_map:
                    job_level_techpack_category_map[job_techpack_category] = []
                job_level_techpack_category_map[job_techpack_category].append(job)

            for techpack_category, techpack_category_jobs in job_level_techpack_category_map.items():
                #ignore Бусад
                if techpack_category == "Бусад":
                    continue
                job_inputs = []
                for job in techpack_category_jobs:
                    job_input = MainSalaryAgentData(**job)
                    job_inputs.append(job_input)

                salary_input = SalaryAgentInput(
                    title=f"{industry} - {job_level} - {techpack_category}",
                    main_data=job_inputs,
                    additional_data=additional_data
                )
                result = await processor.calculate_salary(job_data=salary_input)
                print(f"Salary analysis for industry: {industry}, job level: {job_level}, techpack category: {techpack_category}")
                print(result)
                print("----")
                if result:

                    experience_salary_breakdown = "["
                    experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                    for item in experience_salary_breakdown_list:
                        education_level = item.experience_level
                        min_salary = item.salary_min
                        max_salary = item.salary_max
                        print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                        #dump experience salary breakdown into json string
                        experience_salary_breakdown += json.dumps({
                            "education_level": education_level,
                            "min_salary": min_salary,
                            "max_salary": max_salary
                        })
                    experience_salary_breakdown += "]"
                    data_output = {
                        "title": f"{industry} - {job_level} - {techpack_category} Salary Analysis",
                        "reasoning": result.reasoning,
                        "min_salary": result.min_salary,
                        "max_salary": result.max_salary,
                        "average_salary": result.average_salary,
                        "job_count": len(techpack_category_jobs),
                        "experience_salary_breakdown": experience_salary_breakdown,
                        "type": "industry_job_level_techpack_category",
                        "industry": industry,
                        "job_function": "all",
                        "job_level": job_level,
                        "techpack_category": techpack_category,
                        "year": current_year,
                        "month": current_month,
                    }
                    repository.create(data_output)
                    print(f"Saved salary analysis for industry: {industry}, job level: {job_level}, techpack category: {techpack_category}")

    # function + job level + techpack category combination salary analysis
    for function, function_details in function_map.items():
        #ignore Бусад
        if function == "Бусад":
            continue

        function_jobs = function_details.get("jobs", [])
        function_job_level_map = {}
        for job in function_jobs:
            job_level = job.get("job_level", "Бусад")
            if job_level not in function_job_level_map:
                function_job_level_map[job_level] = []
            function_job_level_map[job_level].append(job)

        for job_level, job_level_jobs in function_job_level_map.items():
            #ignore Бусад
            if job_level == "Бусад":
                continue
            job_level_techpack_category_map = {}
            for job in job_level_jobs:
                job_techpack_category = job.get("job_techpack_category", "Бусад")
                if job_techpack_category not in job_level_techpack_category_map:
                    job_level_techpack_category_map[job_techpack_category] = []
                job_level_techpack_category_map[job_techpack_category].append(job)

            for techpack_category, techpack_category_jobs in job_level_techpack_category_map.items():
                #ignore Бусад
                if techpack_category == "Бусад":
                    continue
                job_inputs = []
                for job in techpack_category_jobs:
                    job_input = MainSalaryAgentData(**job)
                    job_inputs.append(job_input)

                salary_input = SalaryAgentInput(
                    title=f"{function} - {job_level} - {techpack_category}",
                    main_data=job_inputs,
                    additional_data=additional_data
                )
                result = await processor.calculate_salary(job_data=salary_input)
                print(f"Salary analysis for function: {function}, job level: {job_level}, techpack category: {techpack_category}")
                print(result)
                print("----")
                if result:

                    experience_salary_breakdown = "["
                    experience_salary_breakdown_list: List[JobXEducationLevel] = result.experience_salary_breakdown
                    for item in experience_salary_breakdown_list:
                        education_level = item.experience_level
                        min_salary = item.salary_min
                        max_salary = item.salary_max
                        print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                        #dump experience salary breakdown into json string
                        experience_salary_breakdown += json.dumps({
                            "education_level": education_level,
                            "min_salary": min_salary,
                            "max_salary": max_salary
                        }, ensure_ascii=False) + ","

                    experience_salary_breakdown += "]"
                    data_output = {
                        "title": f"{function} - {job_level} - {techpack_category} Salary Analysis",
                        "reasoning": result.reasoning,
                        "min_salary": result.min_salary,
                        "max_salary": result.max_salary,
                        "average_salary": result.average_salary,
                        "job_count": len(techpack_category_jobs),
                        "experience_salary_breakdown": experience_salary_breakdown,
                        "type": "function_job_level_techpack_category",
                        "industry": "all",
                        "job_function": function,
                        "job_level": job_level,
                        "techpack_category": techpack_category,
                        "year": current_year,
                        "month": current_month,
                    }
                    repository.create(data_output)
                    print(f"Saved salary analysis for function: {function}, job level: {job_level}, techpack category: {techpack_category}")
    


async def main():
    """Main function to run all salary calculations sequentially."""
    await industry_salary()  
    # await functional_salary()
    # await job_level_salary()
    # await techpack_category_salary()
    # await all_salary()

if __name__ == "__main__":
    asyncio.run(main())