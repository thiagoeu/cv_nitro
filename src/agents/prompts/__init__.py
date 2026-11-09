"""Subpacote de templates de prompts dos agentes do pipeline."""
from src.agents.prompts.analysis_prompts import JOB_ANALYZER_PROMPT, COMPETENCY_PROMPT
from src.agents.prompts.writer_prompts import (
    build_resume_system_prompt,
    build_resume_user_messages,
    SECTION_PATCH_PROMPT,
    build_cover_letter_prompts,
    PROJECT_INJECTOR_PROMPT,
)
from src.agents.prompts.reviewer_prompts import QUALITY_REVIEWER_PROMPT
from src.agents.prompts.general_prompts import (
    build_general_resume_system_prompt,
    build_general_resume_user_messages,
)

__all__ = [
    "JOB_ANALYZER_PROMPT",
    "COMPETENCY_PROMPT",
    "build_resume_system_prompt",
    "build_resume_user_messages",
    "SECTION_PATCH_PROMPT",
    "build_cover_letter_prompts",
    "PROJECT_INJECTOR_PROMPT",
    "QUALITY_REVIEWER_PROMPT",
    "build_general_resume_system_prompt",
    "build_general_resume_user_messages",
]
