"""Subpacote de formatação, parsing estruturado e renderização HTML A4 de currículos."""
from src.core.formatting.styles import build_a4_html_document
from src.core.formatting.markdown_parser import parse_resume_markdown, serialize_resume_markdown
from src.core.formatting.html_renderer import (
    format_resume_to_html,
    in_experience_or_projects,
    _inline_format,
    _format_contact_item,
)

__all__ = [
    "build_a4_html_document",
    "parse_resume_markdown",
    "serialize_resume_markdown",
    "format_resume_to_html",
    "in_experience_or_projects",
    "_inline_format",
    "_format_contact_item",
]

