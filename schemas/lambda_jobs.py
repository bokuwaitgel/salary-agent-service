from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()


class LambdaJobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="ignore")

    id: Optional[int] = Field(None, description="Primary key from Lambda API")
    title: Optional[str] = Field(None, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    location: Optional[str] = Field(None, description="Job location")
    company_name: Optional[str] = Field(None, description="Company name")
    company_name_mn: Optional[str] = Field(None, description="Company name in Mongolian")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")
    salary_type: Optional[str] = Field(None, description="Salary type (BETWEEN, FIXED, etc.)")
    position_type: Optional[str] = Field(None, description="Position type (EXECUTIVE, SPECIALIST, etc.)")
    engagement_type: Optional[str] = Field(None, description="Engagement type (FULL_TIME, PART_TIME, etc.)")
    pay_type: Optional[str] = Field(None, description="Pay type (MONTHLY, HOURLY, etc.)")
    experience: Optional[int] = Field(None, description="Required experience in years")
    responsibilities: Optional[str] = Field(None, description="Job responsibilities")
    skills: Optional[str] = Field(None, description="Required skills (JSON array as string)")
    commitment: Optional[str] = Field(None, description="Work commitment (ON_SITE, REMOTE, HYBRID)")
    job_category_id: Optional[int] = Field(None, description="Job category ID")
    deadline: Optional[datetime] = Field(None, description="Application deadline")
    slug: Optional[str] = Field(None, description="URL slug for the job")
    view_count: Optional[int] = Field(None, description="Number of views")
    apply_count: Optional[int] = Field(None, description="Number of applications")
    recruiter_id: Optional[int] = Field(None, description="Recruiter ID")
    recruiter_company: Optional[str] = Field(None, description="Recruiter company name")
    recruiter_industry: Optional[str] = Field(None, description="Recruiter industry")
    recruiter_location: Optional[str] = Field(None, description="Recruiter location")
    recruiter_verified: Optional[int] = Field(None, description="Is recruiter verified (1=yes, 0=no)")
    tags: Optional[str] = Field(None, description="Job tags (JSON array as string)")
    status: Optional[str] = Field(None, description="Job status")
    api_created_at: Optional[datetime] = Field(None, description="Created at from API")
    api_updated_at: Optional[datetime] = Field(None, description="Updated at from API")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Record creation timestamp")


class LambdaJobTable(Base):
    __tablename__ = 'lambda_jobs'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    company_name_mn = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_type = Column(String, nullable=True)
    position_type = Column(String, nullable=True)
    engagement_type = Column(String, nullable=True)
    pay_type = Column(String, nullable=True)
    experience = Column(Integer, nullable=True)
    responsibilities = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    commitment = Column(String, nullable=True)
    job_category_id = Column(Integer, nullable=True)
    deadline = Column(DateTime, nullable=True)
    slug = Column(String, nullable=True, index=True)
    view_count = Column(Integer, nullable=True)
    apply_count = Column(Integer, nullable=True)
    recruiter_id = Column(Integer, nullable=True)
    recruiter_company = Column(String, nullable=True)
    recruiter_industry = Column(String, nullable=True)
    recruiter_location = Column(String, nullable=True)
    recruiter_verified = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)
    status = Column(String, nullable=True)
    api_created_at = Column(DateTime, nullable=True)
    api_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)