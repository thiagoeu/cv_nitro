from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    # Entradas do usuário
    job_description: str
    base_resume_md: str
    github_username: str
    
    # Processado pelo Job Analyzer
    job_keywords: List[str]
    job_technologies: List[str]
    
    # Processado pelo GitHub Researcher
    github_repos: List[Dict[str, Any]]
    github_readmes: Dict[str, str]  # repo_name -> readme_content
    
    # Processado pelo Resume Generator
    generated_resume_md: Optional[str]
    
    # Processado pelo Quality Reviewer
    reviewer_feedback: Optional[str]
    reviewer_approved: bool
    review_attempts: int
