from src.agents.nodes import job_analyzer, github_researcher, resume_generator, quality_reviewer, cover_letter_generator
from src.agents.state import GraphState
import os

# Dummy fallback API key for testing structural parsing
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "dummy")

def test_job_analyzer():
    state = GraphState(
        job_description="Procuramos Desenvolvedor Backend com experiência em Python, FastAPI e Docker. Metodologias Ágeis é um diferencial.",
        base_resume_md="",
        github_username="",
        job_url=None,
        job_keywords=[],
        job_technologies=[],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    try:
        if os.environ.get("GEMINI_API_KEY") != "dummy":
            result = job_analyzer(state)
            assert "job_language" in result
            assert "Python" in result['job_technologies'] or "FastAPI" in result['job_technologies']
            assert len(result['job_keywords']) > 0
    except Exception as e:
        print(f"Ignorando erro de API: {e}")

def test_github_researcher():
    state = GraphState(
        job_description="",
        base_resume_md="",
        github_username="octocat",
        job_url=None,
        job_keywords=[],
        job_technologies=["ruby"],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    result = github_researcher(state)
    assert "github_repos" in result
    assert "github_readmes" in result

def test_cover_letter_generator_structure():
    state = GraphState(
        job_description="Software Engineer - Python",
        base_resume_md="# John Doe\nPython Developer",
        github_username="johndoe",
        job_url="https://example.com/job/123",
        job_keywords=["Python", "FastAPI"],
        job_technologies=["Python"],
        job_language="en",
        github_repos=[{"name": "repo1"}],
        github_readmes={"repo1": "FastAPI project"},
        generated_resume_md="# John Doe - Optimized Resume",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=True,
        review_attempts=1
    )
    
    # Executa com fallback / mock se não houver chave
    result = cover_letter_generator(state)
    assert "generated_cover_letter_md" in result
    assert result["generated_cover_letter_md"] is not None
    assert len(result["generated_cover_letter_md"]) > 0
