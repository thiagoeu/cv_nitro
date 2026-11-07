"""Fachada pública para formatação HTML A4 e parsing/serialização estruturada de currículos."""
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
    "format_resume_to_html",
    "parse_resume_markdown",
    "serialize_resume_markdown",
    "in_experience_or_projects",
    "_inline_format",
    "_format_contact_item",
]
