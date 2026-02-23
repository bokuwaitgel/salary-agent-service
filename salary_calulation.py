from src.dependencies import  get_salary_calculation_output_repository
from src.repositories.database import SalaryCalculationOutputRepository
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

async def functional_salary():

    data = open(function_data_path, "r", encoding="utf-8").read()
    function_map = json.loads(data)
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
                "zangia_count": details.get("zangia", 0),
                "lambda_count": details.get("lambda", 0),
                "type": "function",
                "year": 2025,
                "month": 2,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for function: {function}")

async def industry_salary():

    data = open(industry_data_path, "r", encoding="utf-8").read()
    industry_map = json.loads(data)
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
                "type": "industry",
                "year": 2025,
                "month": 2,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for industry: {industry}")

async def job_level_salary():
    data = open(job_level_data_path, "r", encoding="utf-8").read()
    job_level_map = json.loads(data)
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
                "year": 2025,
                "month": 2,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for job level: {job_level}")

async def techpack_category_salary():
    data = open(techpack_category_data_path, "r", encoding="utf-8").read()
    techpack_category_map = json.loads(data)
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
                "year": 2025,
                "month": 2,
            }

            repository.create(data_output)
            print(f"Saved salary analysis for techpack category: {techpack_category}")

async def all_salary():
    # function data
    function = repository.get_by_type("function")
    function_inputs = []
    func_jobs = 0
    func_zangia = 0
    func_lambda = 0
    for item in function:
        dict_item = item.__dict__
        function_input = MainSalaryAgentData(
            title=dict_item.get("title", ""),
            company_name=None,
            job_function=dict_item.get("title", ""),
            job_level=None,
            experience_level=None,
            education_level=None,
            salary_min=dict_item.get("min_salary", None),
            salary_max=dict_item.get("max_salary", None),
            requirements=[],
            job_industry=None
        )
        func_jobs += dict_item.get("job_count", 0)
        func_zangia += dict_item.get("zangia_count", 0)
        func_lambda += dict_item.get("lambda_count", 0)
        function_inputs.append(function_input)

    salary_input = SalaryAgentInput(
        title="All Functional Salary Analysis",
        main_data=function_inputs,
        additional_data={}
    )

    result = await processor.calculate_salary(job_data=salary_input)
    print(f"Salary analysis for all functions")
    print(result)
    print("----")

    
    #save result to database
    if result:
        data_output = {
            "title": "All Functional Salary Analysis",
            "reasoning": result.reasoning, 
            "min_salary": result.min_salary,
            "max_salary": result.max_salary,
            "average_salary": result.average_salary,
            "job_count": func_jobs,
            "zangia_count": func_zangia,
            "lambda_count": func_lambda,
            "type": "all_function",
            "year": 2025,
            "month": 2,
        }

        repository.create(data_output)
        print(f"Saved salary analysis for all functions")

    industry_salary = repository.get_by_type("industry")
    
    industry_inputs = []
    ind_jobs = 0
    ind_zangia = 0
    ind_lambda = 0
    for item in industry_salary:
        dict_item = item.__dict__
        industry_input = MainSalaryAgentData(
            title=dict_item.get("title", ""),
            company_name=None,
            job_function=None,
            job_level=None,
            experience_level=None,
            education_level=None,
            salary_min=dict_item.get("min_salary", None),
            salary_max=dict_item.get("max_salary", None),
            requirements=[],
            job_industry=dict_item.get("title", "")
        )
        ind_jobs += dict_item.get("job_count", 0)
        ind_zangia += dict_item.get("zangia_count", 0)
        ind_lambda += dict_item.get("lambda_count", 0)
        industry_inputs.append(industry_input)
    
    salary_input = SalaryAgentInput(
        title="All Industry Salary Analysis",
        main_data=industry_inputs,
        additional_data={}
    )

    ind_result = await processor.calculate_salary(job_data=salary_input)
    print(f"Salary analysis for all industries")
    print(ind_result)
    print("----")

    if ind_result:
        data_output = {
            "title": "All Industry Salary Analysis",
            "reasoning": ind_result.reasoning, 
            "min_salary": ind_result.min_salary,
            "max_salary": ind_result.max_salary,
            "average_salary": ind_result.average_salary,
            "job_count": ind_jobs,
            "zangia_count": ind_zangia,
            "lambda_count": ind_lambda,
            "type": "all_industry",
            "year": 2025,
            "month": 2,
        }

        repository.create(data_output)
        print(f"Saved salary analysis for all industries")
    
    job_level_salary = repository.get_by_type("job_level")

    job_level_inputs = []
    jl_jobs = 0
    jl_zangia = 0
    jl_lambda = 0

    for item in job_level_salary:
        dict_item = item.__dict__
        job_level_input = MainSalaryAgentData(
            title=dict_item.get("title", ""),
            company_name=None,
            job_function=None,
            job_level=dict_item.get("title", ""),
            experience_level=None,
            education_level=None,
            salary_min=dict_item.get("min_salary", None),
            salary_max=dict_item.get("max_salary", None),
            requirements=[],
            job_industry=None
        )
        jl_jobs += dict_item.get("job_count", 0)
        jl_zangia += dict_item.get("zangia_count", 0)
        jl_lambda += dict_item.get("lambda_count", 0)
        job_level_inputs.append(job_level_input)

    salary_input = SalaryAgentInput(
        title="All Job Level Salary Analysis",
        main_data=job_level_inputs,
        additional_data={}
    )

    jl_result = await processor.calculate_salary(job_data=salary_input)
    print(f"Salary analysis for all job levels")
    print(jl_result)
    print("----")
    if jl_result:
        is_experience_salary_breakdown = True
       
        experience_salary_breakdown = "["
        if is_experience_salary_breakdown:
            experience_salary_breakdown_list = jl_result.experience_salary_breakdown
            for item in experience_salary_breakdown_list:
                education_level = getattr(item, "education_level", None)
                min_salary = getattr(item, "min_salary", None)
                max_salary = getattr(item, "max_salary", None)
                print(f"Education Level: {education_level}, Min Salary: {min_salary}, Max Salary: {max_salary}")
                #dump experience salary breakdown into json string
                experience_salary_breakdown += json.dumps({
                    "education_level": education_level,
                    "min_salary": min_salary,
                    "max_salary": max_salary
                }, ensure_ascii=False) + ","

        experience_salary_breakdown += "]"

        data_output = {
            "title": "All Job Level Salary Analysis",
            "reasoning": jl_result.reasoning, 
            "min_salary": jl_result.min_salary,
            "max_salary": jl_result.max_salary,
            "average_salary": jl_result.average_salary,
            "job_count": jl_jobs,
            "zangia_count": jl_zangia,
            "lambda_count": jl_lambda,
            "type": "all_job_level",
            "year": 2025,
            "month": 2,
        }

        repository.create(data_output)
        print(f"Saved salary analysis for all job levels")
    
    
    techpack_category_salary = repository.get_by_type("techpack_category")
    techpack_category_inputs = []
    tc_jobs = 0
    tc_zangia = 0
    tc_lambda = 0
    for item in techpack_category_salary:
        dict_item = item.__dict__
        techpack_category_input = MainSalaryAgentData(
            title=dict_item.get("title", ""),
            company_name=None,
            job_function=None,
            job_level=None,
            experience_level=None,
            education_level=None,
            salary_min=dict_item.get("min_salary", None),
            salary_max=dict_item.get("max_salary", None),
            requirements=[],
            job_industry=None
        )
        tc_jobs += dict_item.get("job_count", 0)
        tc_zangia += dict_item.get("zangia_count", 0)
        tc_lambda += dict_item.get("lambda_count", 0)
        techpack_category_inputs.append(techpack_category_input)

    salary_input = SalaryAgentInput(
        title="All Techpack Category Salary Analysis",
        main_data=techpack_category_inputs,
        additional_data={}
    )

    tc_result = await processor.calculate_salary(job_data=salary_input)
    print(f"Salary analysis for all techpack categories")
    print(tc_result)
    print("----")
    if tc_result:
        data_output = {
            "title": "All Techpack Category Salary Analysis",
            "reasoning": tc_result.reasoning, 
            "min_salary": tc_result.min_salary,
            "max_salary": tc_result.max_salary,
            "average_salary": tc_result.average_salary,
            "job_count": tc_jobs,
            "zangia_count": tc_zangia,
            "lambda_count": tc_lambda,
            "type": "all_techpack_category",
            "year": 2025,
            "month": 2,
        }

        repository.create(data_output)
        print(f"Saved salary analysis for all techpack categories")



async def main():
    """Main function to run all salary calculations sequentially."""
    await functional_salary()
    await industry_salary()  
    await job_level_salary()
    await techpack_category_salary()
    # await all_salary()

if __name__ == "__main__":
    asyncio.run(main())