from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

class ZangiaJobSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore"
    )

    # Zangia API provides a stable unique identifier under the key `code`.
    # Store it as our DB primary key `id`.
    id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("id", "code"),
        description="Primary key. Populated from Zangia API `code`.",
    )
    company_name: Optional[str] = Field(None, description="Company name in Mongolian")
    company_name_en: Optional[str] = Field(None, description="Company name in English")
    job_level: Optional[str] = Field(None, description="Job level/title")
    job_level_id: Optional[int] = Field(None, description="Job level ID")
    salary_max: Optional[int] = Field(None, description="Maximum salary offered")
    salary_min: Optional[int] = Field(None, description="Minimum salary offered")
    search_additional: Optional[str] = Field(None, description="Additional job search information")
    search_description: Optional[str] = Field(None, description="Job description")
    search_main: Optional[str] = Field(None, description="Main job search text")
    search_requirements: Optional[str] = Field(None, description="Job requirements")
    timetype: Optional[str] = Field(None, description="Type of employment (e.g., full-time)")
    title: Optional[str] = Field(None, description="Job title")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Record creation timestamp")


Base = declarative_base()

class ZangiaJobTable(Base):
    __tablename__ = 'zangia_jobs'

    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=True)
    company_name_en = Column(String, nullable=True)
    job_level = Column(String, nullable=True)
    job_level_id = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_min = Column(Float, nullable=True)
    search_additional = Column(String, nullable=True)
    search_description = Column(String, nullable=True)
    search_main = Column(String, nullable=True)
    search_requirements = Column(String, nullable=True)
    timetype = Column(String, nullable=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
