"""Backward-compatibility shim. All classes have moved to schemas.enums, schemas.models, and schemas.classifier."""
from __future__ import annotations

__all__ = [
    "Category",
    "EducationLevel",
    "ExperienceLevel",
    "JobFunctionCategory",
    "JobIndustryCategory",
    "PositionalCategory",
    "UnifiedJobLevelCategory",
    "JobBenefit",
    "JobClassificationInput",
    "JobClassificationOutput",
    "JobClassificationPaylabInput",
    "JobClassificationPaylabOutput",
    "JobClassifierAgentConfig",
    "JobRequirement",
    "JobClassifierAgent",
]

# Re-export enums
from schemas.enums import (  # noqa: F401
    Category,
    EducationLevel,
    ExperienceLevel,
    JobFunctionCategory,
    JobIndustryCategory,
    PositionalCategory,
    UnifiedJobLevelCategory,
)

# Re-export models
from schemas.models import (  # noqa: F401
    JobBenefit,
    JobClassificationInput,
    JobClassificationOutput,
    JobClassificationPaylabInput,
    JobClassificationPaylabOutput,
    JobClassifierAgentConfig,
    JobRequirement,
)

# Re-export classifier agent
from schemas.classifier import JobClassifierAgent  # noqa: F401
