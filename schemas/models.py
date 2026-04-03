from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from schemas.enums import Category


class JobRequirement(BaseModel):
    """Requirements for a job position."""
    name: str = Field(..., description="Requirement category name (e.g., Education, Experience, Skills). Must be in Mongolian.")
    details: str = Field(..., description="Specific requirement details including qualifications, years of experience, certifications, etc. Must be in Mongolian.")
    importance: str = Field(default="Чухал", description="Importance level: 'Маш чухал' (Critical), 'Чухал' (Important), 'Хүсэлтэй' (Desired)")


class JobBenefit(BaseModel):
    """Benefits and bonuses for a job position."""
    name: str = Field(..., description="Name of the benefit or bonus (e.g., Performance Bonus, Health Insurance). Must be in Mongolian.")
    description: str = Field(..., description="Details about the benefit including conditions, amounts, frequency. Must be in Mongolian.")
    monetary_value: Optional[int] = Field(None, description="Estimated monthly monetary value in MNT if applicable.")


class JobClassificationInput(BaseModel):
    """Input data for job classification."""
    job_title: str = Field(..., description="The job title or position name")
    job_description: Optional[str] = Field(None, description="Full job description text")
    company_name: Optional[str] = Field(None, description="Company or organization name")
    additional_info: Optional[Any] = Field(None, description="Any additional relevant information")
    salary_min: Optional[int] = Field(None, description="Minimum salary offered for the position in MNT")
    salary_max: Optional[int] = Field(None, description="Maximum salary offered for the position in MNT")


class JobClassificationOutput(BaseModel):
    """Output data for job classification."""
    title: str = Field(..., description="Predicted job title")
    job_function: str = Field(..., description="Predicted job function category")
    job_industry: str = Field(..., description="Predicted job industry category")
    category: str = Field(..., description="Predicted Paylab industry/sector category")
    positional_category: str = Field(..., description="Predicted Paylab positional/job title category")
    job_level: str = Field(..., description="Predicted unified job level category")
    salary_min: int = Field(..., description="Minimum salary in MNT based on classification input or estimation")
    salary_max: int = Field(..., description="Maximum salary in MNT based on classification input or estimation")
    experience_level: str = Field(..., description="Predicted experience level category")
    education_level: str = Field(..., description="Predicted education level category")
    company_name: Optional[str] = Field(None, description="Company or organization name if provided in input")
    requirement_reasoning: str = Field(..., description="Explanation of how the input data led to the predicted classifications. This should be 1 to 3 sentences in Mongolian language.")
    requirements: List[JobRequirement] = Field(default_factory=list, description="List of identified job requirements", min_length=0, max_length=3)
    benefits_reasoning: str = Field(..., description="Explanation of how the input data led to the identified benefits and bonuses. This should be 1 to 3 sentences in Mongolian language.")
    benefits: List[JobBenefit] = Field(default_factory=list, description="List of identified job benefits and bonuses", min_length=0, max_length=3)
    confidence_scores: Optional[dict[str, float]] = Field(None, description="Confidence scores for each predicted category")


class JobClassificationPaylabInput(BaseModel):
    """Input data for paylab agent to estimate salary based on job classification output."""
    category: Optional[Category] = Field(None, description="Paylab industry/sector category")
    positional_category: Optional[str] = Field(None, description="Paylab positional/job title category")
    category_min_salary: int = Field(..., description="Minimum salary in MNT for the predicted job category based on market data")
    category_max_salary: int = Field(..., description="Maximum salary in MNT for the predicted job category based on market data")
    title: str = Field(..., description="Predicted job title from classification output")
    salary_min: Optional[int] = Field(None, description="Minimum salary offered for the position in MNT if available")
    salary_max: Optional[int] = Field(None, description="Maximum salary offered for the position in MNT if available")


class JobClassificationPaylabOutput(BaseModel):
    """Output data for paylab agent's salary estimation."""
    salary_min: int = Field(..., description="Estimated minimum salary in MNT based on classification output and input salary information")
    salary_max: int = Field(..., description="Estimated maximum salary in MNT based on classification output and input salary information")
    justification: str = Field(..., description="Justification for the estimated salary range based on market data, industry standards, and specific job characteristics. This should be 1 to 3 sentences in Mongolian language.")


class JobClassifierAgentConfig(BaseModel):
    """Configuration for the Job Classification Agent."""
    system_prompt: str = Field(
        default=(
            "You are a high-precision job classification agent. "
            "Classify each job listing using this strict priority pipeline: Industry -> Function -> Level -> Techpack Category.\n"
            "Decision order rules:\n"
            "1) First decide Job Industry from strongest evidence (company domain, recruiter_industry, description).\n"
            "2) Then decide Job Function consistent with selected Industry and role duties.\n"
            "3) Then decide Unified Job Level from seniority/authority signals in title and responsibilities.\n"
            "4) Then decide Techpack Category, ensuring consistency with Function and Level.\n"
            "5) Then decide Experience Level and Education Level.\n"
            "Consistency rules:\n"
            "- Avoid OTHER unless evidence is genuinely unclear.\n"
            "- Function and Techpack must not contradict each other.\n"
            "- Executive titles must not be labeled as Staff/Specialist unless explicit evidence says otherwise.\n"
            "- Use provided enum values exactly.\n"
            "Extraction rules:\n"
            "- Extract up to 5 requirements and up to 5 benefits from the source text only.\n"
            "- Keep all reasoning and extracted text in Mongolian.\n"
            "Output rules:\n"
            "- Return valid JobClassificationOutput.\n"
            "- Always include short, evidence-based reasoning for requirement_reasoning and benefits_reasoning (1-3 sentences each).\n"
            "- For confidence_scores, include keys: job_industry, job_function, job_level, job_techpack_category, overall with values in [0,1].\n"
            "Batch mode: classify each listing independently and return one output per input in the same order."
        ),
        description="System prompt that guides the agent's behavior and response format."
    )
    system_paylab_prompt: str = Field(
        default=(
            "You are a compensation analyst agent. Based on the job classification output and salary input, provide a salary estimation and justification.\n"
            "1) If salary_min and salary_max are provided in the input, use them directly as the output without modification.\n"
            "2) If salary information is missing, estimate salary_min and salary_max based on the job classification output (job_function, job_industry, job_level, experience_level, education_level) and any salary signals in the job description.\n"
            "3) Provide a clear justification for the estimated salary range based on market data, industry standards, and the specific job characteristics. This should be 1-3 sentences in Mongolian."
        ),
        description="System prompt that guides the paylab agent's behavior and response format."
    )
    model_name: str = Field(default="google-gla:gemini-2.5-flash", description="Name of the language model to use for classification.")
    fallback_model_names: List[str] = Field(
        default_factory=lambda: ["google-gla:gemini-2.5-flash"],
        description="Fallback model names used when the primary model request fails."
    )
    max_batch_size: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of listings sent in one batch model request."
    )
    retry_attempts: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of retries for failed model calls."
    )
    retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0,
        le=30,
        description="Base backoff in seconds between retries."
    )
