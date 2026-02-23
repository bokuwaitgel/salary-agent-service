from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class SalaryCalculationOutput(BaseModel):
    """Output data for salary calculation."""
    reasoning: str = Field(..., description="Explanation of how the salary figures were determined, citing key factors from the job data and market analysis.")
    min_salary: int = Field(..., description="Recommended minimum salary in MNT. Should represent the 25th percentile or entry point for this role in the Mongolian market, considering all job factors and market data.")
    max_salary: int = Field(..., description="Recommended maximum salary in MNT. Should represent the 75th percentile or high-performer compensation for this role, accounting for experience, skills, and company factors.")
    average_salary: int = Field(..., description="Market median/average salary in MNT representing typical compensation for this role. Should fall between min and max, typically closer to min for entry-level roles and closer to max for senior roles.")

class SalaryCalculationOutputTable(Base):
    __tablename__ = 'salary_calculation_output'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    reasoning = Column(Text, nullable=False)
    min_salary = Column(Integer, nullable=False)
    max_salary = Column(Integer, nullable=False)
    average_salary = Column(Integer, nullable=False)
    job_count = Column(Integer, nullable=True)
    zangia_count = Column(Integer, nullable=True)
    lambda_count = Column(Integer, nullable=True)
    type = Column(String, nullable=True)
    experience_salary_breakdown = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)