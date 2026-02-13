from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent


from schemas.base_classifier import JobRequirement




class MainSalaryAgentData(BaseModel):
    """Structured data input for salary analysis with comprehensive job details."""
    title: str = Field(..., description="The job title/position name. This is a primary factor in salary determination as different roles have distinct market rates.")
    company_name: Optional[str] = Field(None, description="The company name. Larger corporations and international companies typically offer higher salaries than startups or smaller local businesses in Mongolia.")
    job_function: Optional[str] = Field(None, description="The functional area (e.g., IT/Software, Finance, Marketing, HR). Critical for salary benchmarking as functions have different market value and demand levels in Mongolia.")
    job_industry: Optional[str] = Field(None, description="The industry sector (e.g., Technology, Mining, Finance, Manufacturing). Industries like mining, finance, and technology typically offer higher compensation in Mongolia compared to retail or hospitality.")
    job_level: Optional[str] = Field(None, description="The hierarchical level (e.g., Executive, Senior Management, Middle Management, Specialist, Staff). Primary salary multiplier: executives earn 3-4x more than specialists, senior management 2-3x, middle management 1.5-2x.")
    education_level: Optional[str] = Field(None, description="Required education (e.g., High School, Bachelor's, Master's, PhD). Higher education typically commands 10-30% salary premium. Master's degrees are valued in technical and managerial roles.")
    experience_level: Optional[str] = Field(None, description="Required experience (e.g., Entry 0-2 years, Junior 2-4 years, Intermediate 4-7 years, Senior 7-12 years, Expert 12+ years). Each level typically represents 20-40% salary increase in Mongolia.")
    requirements: List[JobRequirement] = Field(default_factory=list, description="Specific requirements (certifications, technical skills, language proficiency). Specialized skills (e.g., Python, AWS, bilingual English) can add 15-30% premium. Critical requirements suggest higher compensation.")
    salary_min: Optional[int] = Field(None, description="Stated minimum salary in MNT. Use as baseline reference but validate against market data. If unrealistic, suggest market-aligned range.")
    salary_max: Optional[int] = Field(None, description="Stated maximum salary in MNT. Use as baseline reference but validate against market data. Typical range spread is 20-40% between min and max.")


class SalaryAgentInput(BaseModel):
    """Input data for comprehensive salary analysis."""
    title: str = Field(..., description="The job title/position name. This is a primary factor in salary determination as different roles have distinct market rates.")
    main_data: List[MainSalaryAgentData] = Field(..., description="List of job data entries to analyze. When multiple jobs are provided, analyze them collectively to identify salary patterns, ranges, and statistical distributions for the job category.")
    additional_data: Optional[Any] = Field(None, description="Supplementary market data including: 1) PayLab CSV data with salary benchmarks by job title, function, industry, and experience level. 2) Mongolian salary statistics CSV with national/sectoral averages. Use this data to validate and adjust estimates based on current market conditions.")

class JobXEducationLevel(BaseModel):
    """Structured data for job experience x salary analysis."""
    experience_level: str = Field(..., description="Experience level category (e.g., Entry 0-2 years, Junior 2-4 years, Intermediate 4-7 years, Senior 7-12 years, Expert 12+ years). This is a key driver of salary differences within the same role.")
    # education_level: str = Field(..., description="Education level category (e.g., High School, Bachelor's, Master's, PhD). Higher education levels typically command higher salaries, especially in technical and managerial roles.")
    salary_min: Optional[int] = Field(None, description="Stated minimum salary in MNT for this experience level. Use as a reference point but validate against market data.")
    salary_max: Optional[int] = Field(None, description="Stated maximum salary in MNT for this experience level. Use as a reference point but validate against market data.")
class SalaryAgentOutput(BaseModel):
    """Output data for salary analysis with market-validated estimates."""
    reasoning: str = Field(..., description="Clear 2-4 sentence explanation covering: (1) key factors driving the estimate (job level, industry, experience), (2) how provided market data was used, (3) any adjustments made and why. Cite specific data points when available.")
    min_salary: int = Field(..., description="Recommended minimum salary in MNT. Should be a realistic figure that a hiring manager in Mongolia would recognize as plausible today. Typically represents entry-level compensation for the role, considering all job factors and market data.")
    max_salary: int = Field(..., description="Recommended maximum salary in MNT. Should be a realistic figure that a hiring manager in Mongolia would recognize as plausible today. Typically represents high-performer compensation for this role, accounting for experience, skills, and company factors.")
    reasoning_experience: str = Field(..., description="Explanation of how experience level impacts salary for this role, citing any specific data points or market trends that support the reasoning. This should clarify how compensation typically increases with experience for this job category in Mongolia.")
    experience_salary_breakdown: List[JobXEducationLevel] = Field(..., description="Breakdown of salary estimates by experience level, showing how compensation typically increases with experience for this role. This should reflect the expected salary progression from entry-level to expert within the same job category. If any use market data didn't mentioned then just ignore it.", min_length=0)
    average_salary: int = Field(..., description="Market median/average salary in MNT representing typical compensation for this role. Should fall between min and max, typically closer to min for entry-level roles and closer to max for senior roles.")


class SalaryAgentConfig(BaseModel):
    """Configuration for the Salary Agent."""
    system_prompt: str = Field(
        default=(
            "You are a practical compensation analyst focused on the Mongolian job market. Your goal is to produce a realistic MONTHLY salary range in MNT that a hiring manager in Mongolia would recognize as plausible today. Write like a calm human analyst (not marketing), and be transparent about assumptions.\n\n"
            "You will receive:\n"
            "- One or more job postings (title, industry, function, level, experience, education, requirements, and sometimes a stated salary range).\n"
            "- Optional market files (e.g., PayLab CSV and salary statistics CSV). Use them when available.\n\n"
            "Hard output requirements (must match the output schema):\n"
            "- min_salary, average_salary, max_salary: monthly amounts in MNT (integers).\n"
            "- reasoning: 2–4 sentences, cite the strongest signals and any concrete numbers you used from the provided files.\n"
    
            "Method (be consistent and logical):\n"
            "1) Normalize the role: identify the core role from titles (e.g., 'Accountant', 'Backend Developer', 'HR Specialist') and the seniority/level. If multiple postings are provided, treat them as a cluster and focus on the dominant role/level.\n"
            "2) Build a baseline using market data (preferred):\n"
            "   - If PayLab is provided: find the closest comparable roles (by title/role family) and then narrow by industry/function/experience when possible. Prefer typical/median rows; ignore obvious outliers. Use this to set average_salary.\n"
            "   - If salary statistics are provided: use them as a sanity check (sector or overall). If PayLab and statistics disagree, choose the more role-specific source (usually PayLab) and explain the choice briefly.\n"
            "3) If market files are missing/unusable: fall back to conservative Mongolia-wide heuristics and acknowledge higher uncertainty.\n\n"
            "Adjustment rules (apply only what the input supports; keep adjustments modest unless the data is strong):\n"
            "- Seniority is the strongest factor. Rough guide vs a 'specialist' baseline: entry/staff ~0.6–0.8x, junior ~0.8–1.0x, mid ~1.0–1.2x, senior specialist ~1.2–1.5x, lead/manager ~1.5–2.2x, director ~2.2–3.0x, executive ~3.0–4.0x.\n"
            "- Industry/function: tech, mining, finance often pay a premium. Use PayLab to quantify if possible; otherwise apply a conservative premium/discount.\n"
            "- Experience: each step typically adds ~20–35% (avoid over-compounding).\n"
            "- Scarce skills/certifications/language: add a targeted premium (~10–25%) only if it is clearly a must-have requirement and market-relevant (e.g., cloud certs, strong English for multinational roles).\n"
            "- Company: if the name strongly suggests international/large enterprise, allow a moderate premium (+15–40%). If unknown, do not add a premium.\n\n"
            "Using stated salary_min/salary_max from postings:\n"
            "- Treat them as hints, not truth. Validate against level + market data.\n"
            "- If the stated range is unrealistic, do not anchor to it; correct it and say why in the reasoning.\n\n"
            "Range construction + sanity checks:\n"
            "- Ensure min_salary < average_salary < max_salary.\n"
            "- min_salary approximates entry point; max_salary approximates high-performer compensation.\n"
            "- Typical spread: max ≈ 1.3–1.8 × min (narrower for junior roles, wider for senior/lead roles).\n"
            "- Round all salaries to the nearest 100,000 MNT.\n\n"
            "Reasoning style (2–4 sentences):\n"
            "- Mention the role + level, the top 1–2 drivers (industry/experience/scarce skills/company), and how you used PayLab/statistics (or explicitly say you didn't have them).\n"
            "- Avoid vague phrases like 'based on market data' without specifying what you used.\n"

        ),
        description=(
            "Natural, conversational guidance for accurate salary analysis in the Mongolian market."
        )
    )
    model_name: str = Field(default="google-gla:gemini-3-pro-preview", description="Name of the language model to use for salary estimation.")

class SalaryAgent(Agent):
    config: SalaryAgentConfig
    def __init__(self, config: SalaryAgentConfig):
        self.config = config
        self.agent = Agent(
            system_prompt=config.system_prompt,
            model=config.model_name,
            output_type=SalaryAgentOutput
        )
    
    async def calculate_salary(self, input_data: SalaryAgentInput) -> SalaryAgentOutput:
        main_jobs_list = input_data.main_data
        additional_data_binary = input_data.additional_data

        str_main_jobs_list = [job.model_dump_json() for job in main_jobs_list]  

        #before need to add title of salary result that i want to analize
        title = input_data.title
        jobs_text = "Here is the job data for salary analysis. The title of the job is " + title
        # Combine job data into a single string
        jobs_text += "\n\n".join(str_main_jobs_list)
        user_prompt = f"Job Listings:\n{jobs_text}"
        
        inputs = [user_prompt]
        # If additional_data is a dict, extract the BinaryContent values
        if additional_data_binary:
            if isinstance(additional_data_binary, dict):
                inputs.extend(additional_data_binary.values())
            else:
                inputs.append(additional_data_binary)

        result = await self.agent.run(inputs)   
        print(f"Salary analysis result usage: {result.usage()}")

        return result.output    