from src.service.zangia import get_all_data_and_save
from src.dependencies import get_zangia_sqlalchemy_repository
from src.repositories.database import ZangiaJobRepository

from schemas.techpack import TechpackJobClasifierAgent, TechpackJobClasifierConfig
from src.agent.agent import AgentProcessor
import asyncio
import json
from dotenv import load_dotenv
import os

load_dotenv()

dep = get_zangia_sqlalchemy_repository()

def test_get_all_data_and_save():
    """
    Test fetching all job listings from Zangia API and saving them to the database.
    """
    repository: ZangiaJobRepository = dep
    get_all_data_and_save(repository)

async def main():
    #get all data from database
    repository: ZangiaJobRepository = dep
    datas = repository.get_all()
    print(f"Total jobs in database: {len(datas)}")

    config = TechpackJobClasifierConfig()
    agent = TechpackJobClasifierAgent(config)
    processor = AgentProcessor(agent)

    # Convert SQLAlchemy objects to dictionaries
    job_dicts = []
    for job in datas:
        job_dict = {
            "id": job.id,
            "title": getattr(job, 'title', None),
            "company_name": getattr(job, 'company_name', None),
            "job_level": getattr(job, 'job_level', None),
            "salary_min": getattr(job, 'salary_min', None),
            "salary_max": getattr(job, 'salary_max', None),
            "search_description": getattr(job, 'search_description', None),
            "search_requirements": getattr(job, 'search_requirements', None),
            "search_main": getattr(job, 'search_main', None),
            "timetype": getattr(job, 'timetype', None),
        }
        job_dicts.append(job_dict)
    
    response = await processor.process_batch(input_data=job_dicts, batch_size=100)
    
    #save results to a file
    output_file = "results/zangia_job_classification_results.json"
    os.makedirs("results", exist_ok=True)
    if response:
        # Convert response to serializable format
        results = []
        for item in response:
            # Handle nested lists
            if isinstance(item, list):
                for sub_item in item:
                    if hasattr(sub_item, 'model_dump'):
                        results.append(sub_item.model_dump())
                    else:
                        results.append(sub_item)
            elif hasattr(item, 'model_dump'):
                results.append(item.model_dump())
            else:
                results.append(item)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to {output_file}")
        print(f"Successfully processed {len(results)} jobs")

if __name__ == "__main__":
    asyncio.run(main())
