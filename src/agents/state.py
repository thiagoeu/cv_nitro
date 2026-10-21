import operator
from typing import Annotated, TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    # Entradas do usuário
    job_description: str
    base_resume_md: str
    github_username: str
    job_url: Optional[str]
    
    # Processado pelo Job Analyzer
    job_keywords: List[str]
    job_technologies: List[str]
    job_language: Optional[str]  # ex: 'en', 'pt', 'es'
    
    # Processado pelo GitHub Researcher
    github_repos: List[Dict[str, Any]]
    github_readmes: Dict[str, str]  # repo_name -> readme_content
    
    # Processado pelo Resume Generator
    generated_resume_md: Optional[str]
    
    # Processado pelo Cover Letter Generator
    generated_cover_letter_md: Optional[str]
    
    # Processado pelo Quality Reviewer
    reviewer_feedback: Optional[str]
    reviewer_approved: bool
    review_attempts: int

    # Falhas não fatais (revisor, carta) acumuladas para o app avisar o usuário
    errors: Annotated[List[str], operator.add]
