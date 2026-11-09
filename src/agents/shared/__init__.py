"""Componentes e utilitários compartilhados entre os agentes."""
from src.agents.shared.llm import chat_model, invoke_tracked, response_text, is_truncated
from src.agents.shared.context import (
    job_context,
    portfolio_context,
    format_repos_summary,
    resolve_verified_and_gaps,
)
from src.agents.shared.sections import LABELS, splice_markdown_section, resolve_section, unfilled_placeholders
from src.agents.shared.deterministic_validator import _validate_resume_deterministic
from src.agents.shared.project_injector import inject_projects_from_urls, parse_github_repo_urls

__all__ = [
    "chat_model",
    "invoke_tracked",
    "response_text",
    "is_truncated",
    "job_context",
    "portfolio_context",
    "format_repos_summary",
    "resolve_verified_and_gaps",
    "LABELS",
    "splice_markdown_section",
    "resolve_section",
    "unfilled_placeholders",
    "_validate_resume_deterministic",
    "inject_projects_from_urls",
    "parse_github_repo_urls",
]

