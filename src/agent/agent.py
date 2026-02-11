from abc import ABC, abstractmethod
from pydantic import BaseModel
from pydantic_ai import BinaryContent
from typing import Any, Union, List
from src.logger import logger


# Define an abstract base class for sentiment analysis agents
class SalaryAnalystAgent(ABC):
    @abstractmethod
    async def classify_job(self, input_data: BaseModel | List[BinaryContent] | str):
        pass

    @abstractmethod
    async def classify_job_batch(self, input_data: List[dict] | List[BaseModel] | List[BinaryContent] | BinaryContent):
        pass

    @abstractmethod
    async def calculate_salary(self, job_data: BaseModel | str | BinaryContent | List[BinaryContent]):
        pass

class AgentProcessor:
    def __init__(self, agent: Union[SalaryAnalystAgent, Any]):
        self.agent = agent
        logger.info(f"AgentProcessor initialized with agent: {type(agent).__name__}")

    async def process(self, input_data: BaseModel | List[BinaryContent] | str):
        logger.debug(f"Processing single job with {type(self.agent).__name__}")
        result = await self.agent.classify_job(input_data)
        logger.debug(f"Job processing completed")
        return result
    
    async def process_batch(self, input_data: List[BaseModel] | List[BinaryContent] | BinaryContent):
        result = await self.agent.classify_job_batch(input_data)
        logger.info(f"Batch processing completed")
        return result
    
    async def calculate_salary(self, job_data: BaseModel | str | BinaryContent | List[BinaryContent] | Any):
        logger.debug(f"Calculating salary with {type(self.agent).__name__}")
        result = await self.agent.calculate_salary(job_data)
        logger.debug(f"Salary calculation completed")
        return result
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.process(*args, **kwds)
    