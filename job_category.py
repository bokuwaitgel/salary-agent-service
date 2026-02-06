import json
import asyncio
import os
import pandas as pd

from dotenv import load_dotenv
from pydantic_ai import BinaryContent
load_dotenv()


from schemas.techpack import TechpackJobSalaryCalculatorConfig, TechpackJobSalaryCalculatorAgent
from src.agent.agent import AgentProcessor
from src.service.paylab_data_converter import PaylabDataConverter
from src.service.category_csv_converter import flatten_job_category_data


merged_job_data_path = "results/merged_job_data.json"
# CEO = "Гүйцэтгэх захирал"
# DEPUTY_DIRECTOR = "Дэд захирал"
# CFO = "Санхүү эрхэлсэн захирал"
# GENERAL_ACCOUNTANT = "Ерөнхий нягтлан бодогч"
# ARCHITECTURE_DIRECTOR = "Архитектур шийдэл хариуцсан захирал"
# AGRICULTURE_TECH_DIRECTOR = "Хөдөө аж ахуй хариуцсан технологийн захирал"
# MOBILE_DEVELOPER = "Мобайл хөгжүүлэгч"
# SOFTWARE_ENGINEER = "Программ хангамжийн инженер"
# SENIOR_SOFTWARE_DEVELOPER = "Ахлах программ хөгжүүлэгч"
# IT_SECURITY_ADMIN = "Мэдээллийн аюулгүй байдал болон систем администрат"
# PRODUCT_DESIGN_DIRECTOR = "Бүтээгдэхүүний дизайн хариуцсан захирал"
# PRODUCT_DESIGNER = "Бүтээгдэхүүн хариуцсан дизайнер"
# SENIOR_PRODUCT_DESIGNER = "Бүтээгдэхүүн хариуцсан ахлах дизайнер"
# SENIOR_HR_OFFICER = "Хүний нөөцийн ахлах ажилтан"
# HR_OFFICER = "Хүний нөөцийн ажилтан"
# ADMIN_OFFICER = "Захиргааны ажилтан"
# PROJECT_MANAGEMENT_HEAD = "Төслийн удирдлагын албаны дарга"
# PROJECT_MANAGEMENT_OFFICER = "Төслийн удирдлагын ажилтан"
# PROJECT_MANAGER = "Төслийн менежер"
# PROGRAMMER = "Програмист"
# SENIOR_PROGRAMMER = "Ахлах програмист"
# SYSTEM_DEVELOPER = "Систем хөгжүүлэгч"
# MULTIMEDIA_DESIGNER = "Мультимедиа дизайнер"
# MACHINE_LEARNING_ENGINEER = "Машин сургалтын инженер"
# BUSINESS_DEVELOPMENT_MANAGER = "Бизнес хөгжлийн менежер"
# SENIOR_MACHINE_LEARNING_ENGINEER = "Ахлах машин сургалтын инженер"
# SENIOR_DATA_ENGINEER = "Ахлах дата инженер"
# HEALTH_TECH_DIRECTOR = "Эрүүл мэндийн салбар хариуцсан технологийн захирал"
# FINANCIAL_ANALYST = "Санхүүгийн шинжээч"
# # Add more job categories as needed
# OTHER = "Бусад"

def analyze_merged_job_data(input_path: str, output_path: str):
    """Analyze merged job data and save the analysis to output file."""

    with open(input_path, "r", encoding="utf-8") as f:
        merged_data = json.load(f)

    result = {}    

    for item in merged_data:
        job = item.get("job", {})
        job_category = job.get("job_category") or "Тодорхойгүй"
        print(f"Processing job category: {job_category}")
        if job_category not in result:
            result[job_category] = {
                "count": 0,
                "source_counts": {},
                "jobs": []
            }
        if item["source"] not in result[job_category]["source_counts"]:
            result[job_category]["source_counts"][item["source"]] = 0
        result[job_category]["count"] += 1
        result[job_category]["source_counts"][item["source"]] += 1
        result[job_category]["jobs"].append(item)

    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

async def main():
    config = TechpackJobSalaryCalculatorConfig()
    agent = TechpackJobSalaryCalculatorAgent(config)
    processor = AgentProcessor(agent)
    

    category_data_path = "results/analyzed_job_category_data.json"
    with open(category_data_path, "r", encoding="utf-8") as f:
        category_data = json.load(f)
    
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


    #ignore Tодорхойгүй category
    if "Тодорхойгүй" in category_data:
        del category_data["Тодорхойгүй"]

    #ignore Бусад category
    if "Бусад" in category_data:
        del category_data["Бусад"]

    category_results = {}

    c_list = ["Төслийн удирдлагын албаны дарга", "Програмист", "Мобайл хөгжүүлэгч","Бүтээгдэхүүн хариуцсан ахлах дизайнер", "Хөдөө аж ахуй хариуцсан технологийн захирал"]

    for category in category_data:
        if category not in c_list:
            continue    
        print(f"Processing category: {category}")
        #flatten job data
        flatten_job = flatten_job_category_data(
            {category: category_data[category]}
        )
        #flatten job data to csv
        category_csv_path = f"temp/{category}_jobs.csv"
        flatten_job_df = pd.DataFrame(flatten_job)
        flatten_job_df.to_csv(category_csv_path, index=False, encoding="utf-8-sig")

        input_data = [
            BinaryContent(data=open(category_csv_path, "rb").read(), media_type="text/csv"),
            BinaryContent(data=open(statistic_data_csv_path, "rb").read(), media_type="text/csv"),
            BinaryContent(data=open(paylab_salary_data_csv_path, "rb").read(), media_type="text/csv")
        ]

        response = await processor.calculate_salary(job_data=input_data)


        if response:
            if hasattr(response, 'model_dump'):
                category_results[category] = {
                    **response.model_dump(),
                    "job_count": category_data[category]["count"],
                    "source_counts": category_data[category]["source_counts"]
                }
            else:
                category_results[category] = {
                    **response,
                    "job_count": category_data[category]["count"],
                    "source_counts": category_data[category]["source_counts"]
                }
        

       


    # Save category results to a file
    output_file = "outputs/job_category_salary_analysis_results.json"
    os.makedirs("outputs", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(category_results, f, ensure_ascii=False, indent=2)

    
if __name__ == "__main__":

    # analyze_merged_job_data(merged_job_data_path, "results/analyzed_job_category_data.json")
    asyncio.run(main())