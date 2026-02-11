from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
import json

from schemas.base_classifier import EducationLevel, ExperienceLevel, JobBenefit, JobFunctionCategory, JobIndustryCategory, JobRequirement, JobTechpackCategory, UnifiedJobLevelCategory

Base = declarative_base()

class JobClassificationOutput(BaseModel):
    """Output data for job classification."""
    title: str = Field(..., description="Predicted job title")
    job_function: JobFunctionCategory = Field(..., description="Predicted job function category")
    job_industry: JobIndustryCategory = Field(..., description="Predicted job industry category")
    job_techpack_category: JobTechpackCategory = Field(..., description="Predicted job category based on techpack classification")
    job_level: UnifiedJobLevelCategory = Field(..., description="Predicted unified job level category")
    experience_level: ExperienceLevel = Field(..., description="Predicted experience level category")
    education_level: EducationLevel = Field(..., description="Predicted education level category")
    salary_min: int= Field(..., description="Minimum salary in MNT based on classification input or estimation")
    salary_max: int = Field(..., description="Maximum salary in MNT based on classification input or estimation")
    company_name: Optional[str] = Field(None, description="Company name if the company belongs to a known holding group")
    requirement_reasoning: str = Field(..., description="Explanation of how the input data led to the predicted classifications")
    requirements: List[JobRequirement] = Field(default_factory=list, description="List of identified job requirements", min_length=0, max_length=5)
    benefits_reasoning: str = Field(..., description="Explanation of how the input data led to the identified benefits and bonuses")
    benefits: List[JobBenefit] = Field(default_factory=list, description="List of identified job benefits and bonuses", min_length=0, max_length=5)
    confidence_scores: Optional[dict[str, float]] = Field(None, description="Confidence scores for each predicted category")


class JobClassificationOutputTable(Base):
    __tablename__ = 'job_classification_output'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    job_function = Column(String, nullable=False)
    job_industry = Column(String, nullable=False)
    job_techpack_category = Column(String, nullable=False)
    job_level = Column(String, nullable=False)
    experience_level = Column(String, nullable=False)
    education_level = Column(String, nullable=False)
    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
    company_name = Column(String, nullable=True)
    requirement_reasoning = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)  # JSON string of JobRequirement list
    benefits_reasoning = Column(Text, nullable=False)
    benefits = Column(Text, nullable=True)  # JSON string of JobBenefit list
    confidence_scores = Column(Text, nullable=True)  # JSON string of confidence scores dict
    source_job = Column(String, nullable=True)  # Optional field to link back to the original job listing (e.g., job ID or source name)
