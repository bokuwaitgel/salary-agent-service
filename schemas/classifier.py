from __future__ import annotations

import json
import logging
import random
import re
import asyncio
from typing import Any, List, Optional, cast

from pydantic_ai import Agent

from schemas.enums import (
    Category,
    EducationLevel,
    ExperienceLevel,
    JobFunctionCategory,
    JobIndustryCategory,
    PositionalCategory,
    UnifiedJobLevelCategory,
)
from schemas.models import (
    JobClassificationInput,
    JobClassificationOutput,
    JobClassificationPaylabInput,
    JobClassificationPaylabOutput,
    JobClassifierAgentConfig,
)

logger = logging.getLogger(__name__)

# Maximum allowed length for job_title and job_description to prevent token abuse
_MAX_TITLE_LEN = 500
_MAX_DESCRIPTION_LEN = 15_000

# Pre-computed taxonomy JSON (module-level, built once at import time)
_TAXONOMY_JSON: dict = {
    "job_industry_values": [v.value for v in JobIndustryCategory],
    "job_function_values": [v.value for v in JobFunctionCategory],
    "job_level_values": [v.value for v in UnifiedJobLevelCategory],
    "category_values": [v.value for v in Category],
    "paylab_positional_values": [v.value for v in PositionalCategory],
    "experience_values": [v.value for v in ExperienceLevel],
    "education_values": [v.value for v in EducationLevel],
}

# Pre-computed normalized positional index: normalized_value -> PositionalCategory
_POSITIONAL_INDEX: dict[str, PositionalCategory] = {}
for _cat in PositionalCategory:
    if _cat != PositionalCategory.OTHER:
        _norm = _cat.value.lower().replace("_", " ")
        _norm = re.sub(r"\s+", " ", _norm).strip()
        _POSITIONAL_INDEX[_norm] = _cat

# Pre-computed normalized industry values
_INDUSTRY_NORMS: list[tuple[str, JobIndustryCategory]] = []
for _ind in JobIndustryCategory:
    if _ind != JobIndustryCategory.OTHER:
        _norm = _ind.value.lower().replace("_", " ")
        _norm = re.sub(r"\s+", " ", _norm).strip()
        _INDUSTRY_NORMS.append((_norm, _ind))


def _normalize_text(text: str) -> str:
    cleaned = text.lower().replace("_", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def _sanitize_input(job_input: JobClassificationInput) -> JobClassificationInput:
    """Truncate oversized fields to prevent token abuse."""
    title = (job_input.job_title or "")[:_MAX_TITLE_LEN]
    description = (job_input.job_description or "")[:_MAX_DESCRIPTION_LEN] if job_input.job_description else None
    if title != job_input.job_title or description != job_input.job_description:
        return job_input.model_copy(update={"job_title": title, "job_description": description})
    return job_input


class JobClassifierAgent:
    """Agent for classifying job listings into various categories and extracting requirements and benefits."""

    def __init__(self, config: JobClassifierAgentConfig):
        self.config = config
        self._agent_cache: dict[str, Any] = {}

    def _get_model_candidates(self) -> List[str]:
        candidates = [self.config.model_name, *self.config.fallback_model_names]
        seen: set[str] = set()
        uniq: list[str] = []
        for model in candidates:
            if model and model not in seen:
                seen.add(model)
                uniq.append(model)
        return uniq

    def _get_agent(self, model_name: str, kind: str) -> Agent:
        key = f"{kind}:{model_name}"
        if key not in self._agent_cache:
            if kind == "single":
                self._agent_cache[key] = Agent(model=model_name, system_prompt=self.config.system_prompt, output_type=JobClassificationOutput)
            elif kind == "batch":
                self._agent_cache[key] = Agent(model=model_name, system_prompt=self.config.system_prompt, output_type=List[JobClassificationOutput])
            elif kind == "paylab":
                self._agent_cache[key] = Agent(model=model_name, system_prompt=self.config.system_paylab_prompt, output_type=str)
        return self._agent_cache[key]

    @staticmethod
    def _parse_paylab_json_output(raw_text: str) -> List[JobClassificationPaylabOutput]:
        payload_text = (raw_text or "").strip()
        if payload_text.startswith("```"):
            payload_text = payload_text.strip("`")
            if payload_text.lower().startswith("json"):
                payload_text = payload_text[4:].strip()

        payload = json.loads(payload_text)
        if not isinstance(payload, list):
            raise ValueError("Paylab output is not a JSON array.")

        parsed: List[JobClassificationPaylabOutput] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Paylab output item is not a JSON object.")
            parsed.append(
                JobClassificationPaylabOutput(
                    salary_min=int(item.get("salary_min", 0) or 0),
                    salary_max=int(item.get("salary_max", 0) or 0),
                    justification=str(item.get("justification", "") or "").strip(),
                )
            )
        return parsed

    def _match_industry_from_input(self, job_input: JobClassificationInput) -> Optional[JobIndustryCategory]:
        recruiter_industry = ""
        if isinstance(job_input.additional_info, dict):
            recruiter_industry = str(job_input.additional_info.get("recruiter_industry", "") or "")

        candidate_texts = [
            recruiter_industry,
            job_input.company_name or "",
            job_input.job_title or "",
            job_input.job_description or "",
        ]
        merged = _normalize_text(" ".join(candidate_texts))
        recruiter_norm = _normalize_text(recruiter_industry)

        if recruiter_norm:
            for industry_norm, industry in _INDUSTRY_NORMS:
                if recruiter_norm == industry_norm or recruiter_norm in industry_norm or industry_norm in recruiter_norm:
                    return industry

        for industry_norm, industry in _INDUSTRY_NORMS:
            if industry_norm and industry_norm in merged:
                return industry

        return None

    def _infer_function_from_title(self, title: str) -> Optional[JobFunctionCategory]:
        title_norm = _normalize_text(title)
        keyword_map: dict[JobFunctionCategory, list[str]] = {
            JobFunctionCategory.IT_TELECOM: ["developer", "software", "програм", "it", "систем", "ml", "data engineer", "devops", "qa", "security admin"],
            JobFunctionCategory.FINANCE_ACCOUNTING: ["санхүү", "нягтлан", "accountant", "finance", "cfo", "auditor", "эдийн засагч"],
            JobFunctionCategory.HR: ["хүний нөөц", "hr", "talent", "recruit"],
            JobFunctionCategory.MARKETING_PR: ["маркетинг", "brand", "pr", "контент", "social media"],
            JobFunctionCategory.SALES: ["борлуулалт", "sales", "account manager", "business sales"],
            JobFunctionCategory.BUSINESS_DEVELOPMENT: ["бизнес хөгжил", "business development", "partnership"],
            JobFunctionCategory.PROJECT_ALL: ["project manager", "төслийн", "pmo", "program manager"],
            JobFunctionCategory.ENGINEERING_TECHNICAL: ["инженер", "техник", "maintenance", "architect"],
            JobFunctionCategory.ADMINISTRATION: ["захиргаа", "office", "admin"],
            JobFunctionCategory.CUSTOMER_SERVICE: ["customer", "харилцагч", "call center", "support"],
            JobFunctionCategory.PROCUREMENT: ["худалдан авалт", "procurement", "sourcing", "buyer"],
            JobFunctionCategory.LEGAL: ["хууль", "legal", "compliance"],
            JobFunctionCategory.DISTRIBUTION_TRANSPORT: ["логистик", "тээвэр", "warehouse", "driver", "жолооч"],
            JobFunctionCategory.EXECUTIVE_MANAGEMENT: ["гүйцэтгэх захирал", "ceo", "general director", "ерөнхий захирал", "director"],
        }

        for function, keywords in keyword_map.items():
            if any(k in title_norm for k in keywords):
                return function
        return None

    def _infer_level_from_title(self, title: str) -> Optional[UnifiedJobLevelCategory]:
        title_norm = _normalize_text(title)

        if any(k in title_norm for k in ["ceo", "гүйцэтгэх захирал", "chief", "ерөнхий захирал"]):
            return UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT
        if any(k in title_norm for k in ["захирал", "director", "head of", "албаны дарга"]):
            return UnifiedJobLevelCategory.SENIOR_MANAGEMENT
        if any(k in title_norm for k in ["менежер", "manager", "supervisor", "team lead", "ахлагч"]):
            return UnifiedJobLevelCategory.MIDDLE_MANAGEMENT
        if any(k in title_norm for k in ["senior", "ахлах", "principal", "lead"]):
            return UnifiedJobLevelCategory.SPECIALIST_SENIOR
        if any(k in title_norm for k in ["engineer", "developer", "analyst", "мэргэжилтэн", "инженер", "дизайнер", "нягтлан"]):
            return UnifiedJobLevelCategory.SPECIALIST
        if any(k in title_norm for k in ["ажилтан", "assistant", "оператор", "туслах", "жолооч", "касс"]):
            return UnifiedJobLevelCategory.STAFF

        return None

    def _match_positional_from_title(self, title: str) -> Optional[PositionalCategory]:
        title_norm = _normalize_text(title)
        if title_norm in _POSITIONAL_INDEX:
            return _POSITIONAL_INDEX[title_norm]
        for norm_value, cat in _POSITIONAL_INDEX.items():
            if norm_value in title_norm:
                return cat
        return None

    def _build_classification_payload(self, job_input: JobClassificationInput) -> str:
        payload = {
            "classification_priority": ["job_industry", "job_function", "job_level", "category", "positional_category"],
            "job": job_input.model_dump(),
            "taxonomy": _TAXONOMY_JSON,
        }
        return json.dumps(payload, ensure_ascii=False)

    def _refine_output(self, job_input: JobClassificationInput, output: JobClassificationOutput) -> JobClassificationOutput:
        title = job_input.job_title or output.title

        inferred_industry = self._match_industry_from_input(job_input)
        inferred_function = self._infer_function_from_title(title)
        inferred_level = self._infer_level_from_title(title)
        inferred_positional = self._match_positional_from_title(title)

        if inferred_industry and output.job_industry == JobIndustryCategory.OTHER.value:
            output.job_industry = inferred_industry.value

        if inferred_function and output.job_function == JobFunctionCategory.OTHER.value:
            output.job_function = inferred_function.value

        if inferred_level and output.job_level in {UnifiedJobLevelCategory.STAFF.value, UnifiedJobLevelCategory.SPECIALIST.value}:
            if inferred_level in {UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT, UnifiedJobLevelCategory.SENIOR_MANAGEMENT, UnifiedJobLevelCategory.MIDDLE_MANAGEMENT, UnifiedJobLevelCategory.SPECIALIST_SENIOR}:
                output.job_level = inferred_level.value

        if inferred_positional and output.positional_category in {"Other", "other", ""}:
            output.positional_category = inferred_positional.value

        if output.job_function == JobFunctionCategory.EXECUTIVE_MANAGEMENT.value and output.job_level in {UnifiedJobLevelCategory.STAFF.value, UnifiedJobLevelCategory.SPECIALIST.value}:
            output.job_level = UnifiedJobLevelCategory.SENIOR_MANAGEMENT.value

        if output.job_level == UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT.value and output.job_function == JobFunctionCategory.OTHER.value:
            output.job_function = JobFunctionCategory.EXECUTIVE_MANAGEMENT.value

        if output.confidence_scores is None:
            output.confidence_scores = {}

        output.confidence_scores.setdefault("job_industry", 0.75 if inferred_industry else 0.6)
        output.confidence_scores.setdefault("job_function", 0.75 if inferred_function else 0.6)
        output.confidence_scores.setdefault("job_level", 0.75 if inferred_level else 0.6)
        output.confidence_scores.setdefault("positional_category", 0.75 if inferred_positional else 0.6)
        if "overall" not in output.confidence_scores:
            vals = [
                output.confidence_scores.get("job_industry", 0.6),
                output.confidence_scores.get("job_function", 0.6),
                output.confidence_scores.get("job_level", 0.6),
                output.confidence_scores.get("positional_category", 0.6),
            ]
            output.confidence_scores["overall"] = round(sum(vals) / len(vals), 3)

        return output

    def _retry_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        return self.config.retry_backoff_seconds * (2 ** attempt) + random.uniform(0, 1)

    async def _run_single_with_fallback(self, payload: str, job_input: JobClassificationInput) -> JobClassificationOutput:
        last_error: Optional[Exception] = None
        for model_name in self._get_model_candidates():
            agent = self._get_agent(model_name, "single")
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    response = await agent.run(payload)
                    logger.info("Single classification usage: %s", response.usage())
                    model_output = cast(JobClassificationOutput, response.output)
                    return self._refine_output(job_input, model_output)
                except Exception as exc:
                    last_error = exc
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self._retry_delay(attempt))
                    else:
                        logger.warning("Single classification failed on model=%s: %s", model_name, exc)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Single classification failed for unknown reason.")

    async def _run_batch_chunk_with_fallback(self, job_inputs: List[JobClassificationInput]) -> List[JobClassificationOutput]:
        payloads = [self._build_classification_payload(item) for item in job_inputs]

        for model_name in self._get_model_candidates():
            agent = self._get_agent(model_name, "batch")
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    result = await agent.run(payloads)
                    logger.info("Batch classification completed. Usage: %s", result.usage())
                    batch_output = cast(List[JobClassificationOutput], result.output)
                    outputs: List[JobClassificationOutput] = []
                    for raw_input, classified in zip(job_inputs, batch_output):
                        outputs.append(self._refine_output(raw_input, classified))

                    if len(outputs) == len(job_inputs):
                        return outputs

                    # Mismatch: immediately take partial results, classify remaining individually
                    missing_inputs = job_inputs[len(outputs):]
                    logger.warning(
                        "Batch output size mismatch (model=%s attempt=%d): expected=%d got=%d, classifying remaining %d individually",
                        model_name, attempt + 1, len(job_inputs), len(outputs), len(missing_inputs),
                    )
                    for item in missing_inputs:
                        payload = self._build_classification_payload(item)
                        outputs.append(await self._run_single_with_fallback(payload, item))
                    return outputs
                except Exception as exc:
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self._retry_delay(attempt))
                    else:
                        logger.warning("Batch chunk failed on model=%s: %s", model_name, exc)

        # No batch succeeded at all — fall back to single calls for everything
        logger.info("Falling back to single classification for all %d items", len(job_inputs))
        single_outputs: List[JobClassificationOutput] = []
        for item in job_inputs:
            payload = self._build_classification_payload(item)
            single_outputs.append(await self._run_single_with_fallback(payload, item))
        return single_outputs

    async def classify_job(self, job_input: JobClassificationInput) -> JobClassificationOutput:
        """Classify a job listing and extract requirements and benefits."""
        job_input = _sanitize_input(job_input)
        payload = self._build_classification_payload(job_input)
        return await self._run_single_with_fallback(payload, job_input)

    async def classify_job_batch(self, job_inputs: List[JobClassificationInput]) -> List[JobClassificationOutput]:
        """Classify multiple job listings in batch."""
        job_inputs = [_sanitize_input(item) for item in job_inputs]
        logger.info("Classifying batch of %d job listings...", len(job_inputs))
        outputs: List[JobClassificationOutput] = []
        step = self.config.max_batch_size
        for i in range(0, len(job_inputs), step):
            chunk = job_inputs[i:i + step]
            chunk_outputs = await self._run_batch_chunk_with_fallback(chunk)
            outputs.extend(chunk_outputs)
        logger.info("Batch classification produced %d outputs.", len(outputs))
        return outputs

    async def paylab_job_batch(self, job_inputs: List[JobClassificationPaylabInput]) -> List[JobClassificationPaylabOutput]:
        """Run paylab agent to estimate salary for multiple job classifications in batch."""
        logger.info("Running paylab agent for batch of %d job classifications...", len(job_inputs))
        inputs = ""
        for item in job_inputs:
            category_value = item.category.value if item.category is not None else "None"
            inputs += f"Category: {category_value}, Category Min Salary: {item.category_min_salary}, Category Max Salary: {item.category_max_salary}, Title: {item.title}, Salary Min: {item.salary_min}, Salary Max: {item.salary_max}\n"
        inputs += (
            "\nReturn ONLY a valid JSON array. "
            "Each item must have keys: salary_min (int), salary_max (int), justification (string). "
            "Do not include markdown, explanation, or extra keys. "
            "The output array length must exactly match the number of input rows in the same order."
        )

        last_error: Optional[Exception] = None
        for model_name in self._get_model_candidates():
            agent = self._get_agent(model_name, "paylab")
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    response = await agent.run(inputs)
                    logger.info("Paylab batch usage: %s", response.usage())
                    paylab_output = self._parse_paylab_json_output(cast(str, response.output))
                    if len(paylab_output) == len(job_inputs):
                        return paylab_output
                    raise RuntimeError(f"Paylab batch output size mismatch. expected={len(job_inputs)} got={len(paylab_output)}")
                except Exception as exc:
                    last_error = exc
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self._retry_delay(attempt))
                    else:
                        logger.warning("Paylab batch failed on model=%s: %s", model_name, exc)
        if last_error is not None:
            raise last_error
        raise RuntimeError("Paylab batch classification failed for unknown reason.")
