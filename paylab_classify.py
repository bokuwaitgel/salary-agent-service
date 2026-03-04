from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Tuple, cast

from dotenv import load_dotenv
from pydantic import BaseModel

from schemas.base_classifier import (
    JobClassificationPaylabInput,
    JobClassificationPaylabOutput,
    JobClassifierAgent,
    JobClassifierAgentConfig,
    ExperienceLevel,
    EducationLevel,
    JobFunctionCategory,
    JobIndustryCategory,
    JobTechpackCategory,
    UnifiedJobLevelCategory,
)
from src.agent.agent import AgentProcessor
from src.dependencies import get_classifier_output_repository
from src.repositories.database import JobClassificationOutputRepository


load_dotenv()

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


PAYLAB_JSON_PATH = Path(os.getenv("PAYLAB_JSON_PATH", "additional_data/paylab_job_data.json"))
PAYLAB_BATCH_SIZE = max(1, int(os.getenv("PAYLAB_CLASSIFY_BATCH_SIZE", "100")))
PAYLAB_SUB_BATCH_SIZE = max(1, int(os.getenv("PAYLAB_CLASSIFY_SUB_BATCH_SIZE", "25")))
PAYLAB_START_INDEX = max(0, int(os.getenv("PAYLAB_CLASSIFY_START_INDEX", "0")))
PAYLAB_LIMIT = int(os.getenv("PAYLAB_CLASSIFY_LIMIT", "0"))
PAYLAB_CONCURRENT_TASKS = max(1, int(os.getenv("PAYLAB_CLASSIFY_CONCURRENCY", "4")))


def _normalize_paylab_category(value: Any) -> JobTechpackCategory:
    raw = str(value or "").strip()
    if not raw:
        return JobTechpackCategory.OTHER

    try:
        return JobTechpackCategory(raw)
    except ValueError:
        pass

    by_name = raw.upper().replace(" ", "_")
    if by_name in JobTechpackCategory.__members__:
        return JobTechpackCategory[by_name]

    lowered = raw.lower()

    alias_map: dict[str, JobTechpackCategory] = {
        "administration": JobTechpackCategory.ADMIN_OFFICER,
        "information technology": JobTechpackCategory.SOFTWARE_ENGINEER,
        "technology, development": JobTechpackCategory.SOFTWARE_ENGINEER,
        "human resources": JobTechpackCategory.HR_OFFICER,
        "economy, finance, accountancy": JobTechpackCategory.FINANCIAL_ANALYST,
        "banking": JobTechpackCategory.FINANCIAL_ANALYST,
        "insurance": JobTechpackCategory.FINANCIAL_ANALYST,
        "top management": JobTechpackCategory.CEO,
        "management": JobTechpackCategory.PROJECT_MANAGER,
        "marketing, advertising, pr": JobTechpackCategory.BUSINESS_DEVELOPMENT_MANAGER,
    }
    mapped = alias_map.get(lowered)
    if mapped:
        return mapped

    contains_map: list[tuple[str, JobTechpackCategory]] = [
        ("information technology", JobTechpackCategory.SOFTWARE_ENGINEER),
        ("technology", JobTechpackCategory.SOFTWARE_ENGINEER),
        ("telecommunications", JobTechpackCategory.IT_SECURITY_ADMIN),
        ("finance", JobTechpackCategory.FINANCIAL_ANALYST),
        ("bank", JobTechpackCategory.FINANCIAL_ANALYST),
        ("insurance", JobTechpackCategory.FINANCIAL_ANALYST),
        ("human resources", JobTechpackCategory.HR_OFFICER),
        ("marketing", JobTechpackCategory.BUSINESS_DEVELOPMENT_MANAGER),
        ("top management", JobTechpackCategory.CEO),
        ("management", JobTechpackCategory.PROJECT_MANAGER),
    ]
    for keyword, mapped_category in contains_map:
        if keyword in lowered:
            return mapped_category

    return JobTechpackCategory.OTHER


def _derive_job_function(category_name: str, title: str) -> JobFunctionCategory:
    text = f"{category_name} {title}".lower()

    contains_map: list[tuple[list[str], JobFunctionCategory]] = [
        (["information technology", "technology", "telecommunications", "developer", "software", "it"], JobFunctionCategory.IT_TELECOM),
        (["economy", "finance", "account", "bank", "insurance", "leasing"], JobFunctionCategory.FINANCE_ACCOUNTING),
        (["human resources", "hr"], JobFunctionCategory.HR),
        (["marketing", "advertising", "pr"], JobFunctionCategory.MARKETING_PR),
        (["customer support", "customer service"], JobFunctionCategory.CUSTOMER_SERVICE),
        (["law", "legislation", "legal"], JobFunctionCategory.LEGAL),
        (["transport", "haulage", "logistics"], JobFunctionCategory.DISTRIBUTION_TRANSPORT),
        (["medicine", "social care", "pharmaceutical"], JobFunctionCategory.HEALTHCARE),
        (["security", "protection"], JobFunctionCategory.SECURITY),
        (["construction", "engineering", "industry", "production", "mining", "metallurgy"], JobFunctionCategory.ENGINEERING_TECHNICAL),
        (["top management", "management"], JobFunctionCategory.EXECUTIVE_MANAGEMENT),
        (["administration", "public administration"], JobFunctionCategory.ADMINISTRATION),
        (["commerce", "sales"], JobFunctionCategory.SALES),
    ]

    for keywords, function in contains_map:
        if any(keyword in text for keyword in keywords):
            return function

    return JobFunctionCategory.OTHER


def _derive_job_level(category_name: str, title: str) -> UnifiedJobLevelCategory:
    text = f"{category_name} {title}".lower()
    if any(keyword in text for keyword in ["top management", "ceo", "chief", "executive"]):
        return UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT
    if "management" in text or "director" in text:
        return UnifiedJobLevelCategory.MIDDLE_MANAGEMENT
    if any(keyword in text for keyword in ["senior", "lead", "ахлах"]):
        return UnifiedJobLevelCategory.SPECIALIST_SENIOR
    return UnifiedJobLevelCategory.SPECIALIST


def _derive_job_industry(category_name: str, title: str) -> JobIndustryCategory:
    text = f"{category_name} {title}".lower()

    contains_map: list[tuple[list[str], JobIndustryCategory]] = [
        (["information technology", "telecommunications", "technology"], JobIndustryCategory.INFORMATION_COMMUNICATION),
        (["bank", "finance", "insurance", "leasing", "account"], JobIndustryCategory.FINANCE_INSURANCE),
        (["construction", "real estate"], JobIndustryCategory.CONSTRUCTION),
        (["agriculture", "food industry", "forestry"], JobIndustryCategory.AGRICULTURE_FORESTRY_FISHING_HUNTING),
        (["education", "science", "research"], JobIndustryCategory.EDUCATION),
        (["medicine", "social care", "pharmaceutical"], JobIndustryCategory.HEALTHCARE_SOCIAL_ASSISTANCE),
        (["transport", "haulage", "logistics"], JobIndustryCategory.TRANSPORTATION_WAREHOUSING),
        (["public administration", "self-governance"], JobIndustryCategory.PUBLIC_ADMINISTRATION_DEFENSE_SOCIAL_SECURITY),
        (["commerce", "retail", "wholesale"], JobIndustryCategory.WHOLESALE_RETAIL_TRADE_REPAIR_MOTOR_VEHICLES_MOTORCYCLES),
        (["mining", "metallurgy"], JobIndustryCategory.MINING_QUARRYING_OIL_GAS_EXTRACTION),
        (["production", "mechanical", "chemical", "textile", "wood", "car industry"], JobIndustryCategory.MANUFACTURING),
        (["arts", "culture", "journalism", "media"], JobIndustryCategory.ARTS_ENTERTAINMENT_RECREATION),
        (["tourism", "gastronomy", "hotel"], JobIndustryCategory.ACCOMMODATION_FOOD_SERVICES),
        (["water management", "environment"], JobIndustryCategory.WATER_SEWERAGE_WASTE_MANAGEMENT_REMEDIATION),
        (["law", "legislation", "legal"], JobIndustryCategory.PROFESSIONAL_SCIENTIFIC_TECHNICAL_SERVICES),
        (["service industries", "general labour", "customer support"], JobIndustryCategory.OTHER_SERVICES),
    ]

    for keywords, industry in contains_map:
        if any(keyword in text for keyword in keywords):
            return industry

    return JobIndustryCategory.OTHER


def _current_period() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    year = os.getenv("PAYLAB_CLASSIFY_YEAR", str(now.year))
    month = os.getenv("PAYLAB_CLASSIFY_MONTH", f"{now.month-1:02d}")
    return year, month


def _load_paylab_jobs() -> list[dict[str, Any]]:
    if not PAYLAB_JSON_PATH.exists():
        raise FileNotFoundError(f"Paylab JSON not found: {PAYLAB_JSON_PATH}")

    with PAYLAB_JSON_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for category_item in payload.get("jobs_data", []):
        category_name = str(category_item.get("category_name", "")).strip()
        category_min = category_item.get("min_salary")
        category_max = category_item.get("max_salary")

        for job in category_item.get("job_list", []):
            title = str(job.get("job_title", "")).strip()
            job_url = str(job.get("job_url", "")).strip()

            if not title:
                continue

            dedupe_key = f"{category_name}|{title}|{job_url}".lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            salary_min = job.get("min_salary")
            salary_max = job.get("max_salary")

            if isinstance(salary_min, (int, float)) and salary_min <= 0:
                salary_min = None
            if isinstance(salary_max, (int, float)) and salary_max <= 0:
                salary_max = None

            rows.append(
                {
                    "category_name": category_name,
                    "category_min_salary": category_min,
                    "category_max_salary": category_max,
                    "job_title": title,
                    "job_url": job_url,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                }
            )

    return rows


def _build_job_id(row: dict[str, Any]) -> str:
    raw = f"paylab_1|{row.get('category_name','')}|{row.get('job_title','')}|{row.get('job_url','')}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]
    return f"paylab_{digest}"


def _to_classifier_input(row: dict[str, Any]) -> JobClassificationPaylabInput:
    category = row.get("category_name") or ""
    title = row.get("job_title") or ""
    url = row.get("job_url") or ""

    desc = (
        f"Paylab benchmark role. Category: {category}. "
        f"Reference title: {title}. Source URL: {url}."
    )

    return JobClassificationPaylabInput(
        category=_normalize_paylab_category(category),
        category_min_salary=row.get("category_min_salary", 0) or 0,
        category_max_salary=row.get("category_max_salary", 0) or 0,
        title=title,
        salary_min=row.get("salary_min"),
        salary_max=row.get("salary_max"),
    )


def _to_output_dict(
    output: JobClassificationPaylabOutput,
    row: dict[str, Any],
    year: str,
    month: str,
) -> dict[str, Any]:
    category = _normalize_paylab_category(row.get("category_name"))
    title = str(row.get("job_title") or "")
    category_name = str(row.get("category_name") or "")
    job_function = _derive_job_function(category_name=category_name, title=title)
    job_level = _derive_job_level(category_name=category_name, title=title)
    job_industry = _derive_job_industry(category_name=category_name, title=title)

    return {
        "id": _build_job_id(row),
        "title": title,
        "job_function": job_function,
        "job_industry": job_industry,
        "job_techpack_category": category,
        "job_level": job_level,
        "experience_level": ExperienceLevel.INTERMEDIATE,
        "education_level": EducationLevel.BACHELOR,
        "salary_min": output.salary_min,
        "salary_max": output.salary_max,
        "company_name": "Paylab Market Dataset",
        "requirement_reasoning": "Paylab dataset salary estimation entry.",
        "requirements": json.dumps([], ensure_ascii=False),
        "benefits_reasoning": str(output.justification or ""),
        "benefits": json.dumps([], ensure_ascii=False),
        "confidence_scores": json.dumps({"overall": 0.5}, ensure_ascii=False),
        "year": year,
        "month": month,
        "source_job": "paylab",
    }


async def _classify_sub_batch(
    processor: AgentProcessor,
    sub_batch: list[tuple[JobClassificationPaylabInput, dict[str, Any]]],
) -> list[tuple[JobClassificationPaylabOutput, dict[str, Any]]]:
    inputs = [item[0] for item in sub_batch]
    base_inputs: list[BaseModel] = [cast(BaseModel, item) for item in inputs]
    try:
        raw_outputs = await processor.process_paylab_batch(base_inputs)
        outputs = cast(list[JobClassificationPaylabOutput], raw_outputs or [])
    except Exception:
        outputs = []
        for single_input in inputs:
            single_output = cast(List[JobClassificationPaylabOutput], await processor.process_paylab_batch([single_input]))
            outputs.extend(single_output)
    
    paired: list[tuple[JobClassificationPaylabOutput, dict[str, Any]]] = []
    for output, (_, row) in zip(outputs, sub_batch):
        paired.append((output, row))
    return paired


async def main() -> None:
    rows = _load_paylab_jobs()
    if PAYLAB_START_INDEX:
        rows = rows[PAYLAB_START_INDEX:]
    if PAYLAB_LIMIT > 0:
        rows = rows[:PAYLAB_LIMIT]

    print(f"Loaded Paylab jobs for classification: {len(rows)}")
    if not rows:
        return

    repository: JobClassificationOutputRepository = get_classifier_output_repository()

    config = JobClassifierAgentConfig()
    config.max_batch_size = PAYLAB_SUB_BATCH_SIZE

    agent = JobClassifierAgent(config=config)
    processor = AgentProcessor(agent)

    year, month = _current_period()

    prepared: list[tuple[JobClassificationPaylabInput, dict[str, Any]]] = [
        (_to_classifier_input(row), row) for row in rows
    ]

    saved = 0
    for batch_start in range(0, len(prepared), PAYLAB_BATCH_SIZE):
        batch = prepared[batch_start : batch_start + PAYLAB_BATCH_SIZE]

        tasks = []
        for sub_start in range(0, len(batch), PAYLAB_SUB_BATCH_SIZE):
            sub_batch = batch[sub_start : sub_start + PAYLAB_SUB_BATCH_SIZE]
            tasks.append(asyncio.create_task(_classify_sub_batch(processor, sub_batch)))

        results = await asyncio.gather(*tasks)

        for result_group in results:
            for output, row in result_group:
                repository.create(_to_output_dict(output=output, row=row, year=year, month=month))
                saved += 1

        print(
            f"Processed batch {batch_start // PAYLAB_BATCH_SIZE + 1} | "
            f"saved so far: {saved}/{len(prepared)}"
        )

    print(f"Paylab classification done. Total saved/seen: {saved}/{len(prepared)}")


if __name__ == "__main__":
    asyncio.run(main())
