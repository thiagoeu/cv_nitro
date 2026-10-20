from unittest.mock import patch, MagicMock
from src.agents.nodes import (
    job_analyzer,
    github_researcher,
    resume_generator,
    quality_reviewer,
    cover_letter_generator
)
from src.agents.graph import route_after_review
from src.agents.state import GraphState
import os

# Dummy fallback API key for testing structural parsing
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "dummy")

def test_github_researcher_invalid_username():
    state = GraphState(
        job_description="",
        base_resume_md="",
        github_username="../../invalid/path",
        job_url=None,
        job_keywords=[],
        job_technologies=["python"],
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
    assert result["github_repos"] == []
    assert result["github_readmes"] == {}

def test_github_researcher_with_mock():
    state = GraphState(
        job_description="",
        base_resume_md="",
        github_username="octocat",
        job_url=None,
        job_keywords=[],
        job_technologies=["python"],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    mock_repos_resp = MagicMock()
    mock_repos_resp.status_code = 200
    mock_repos_resp.json.return_value = [
        {
            "name": "python-project",
            "description": "A Python backend",
            "language": "Python",
            "html_url": "https://github.com/octocat/python-project",
            "default_branch": "main"
        }
    ]
    
    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 200
    import base64
    mock_readme_resp.json.return_value = {
        "content": base64.b64encode(b"# Python Project\nDocumentation").decode("utf-8")
    }

    with patch("requests.get") as mock_get:
        mock_get.side_effect = [mock_repos_resp, mock_readme_resp]
        result = github_researcher(state)
        
        # Valida que timeout foi repassado nas chamadas requests
        assert mock_get.call_count == 2
        for call_args in mock_get.call_args_list:
            assert "timeout" in call_args.kwargs
            assert call_args.kwargs["timeout"] == (5.0, 10.0)
            
        assert len(result["github_repos"]) == 1
        assert "python-project" in result["github_readmes"]
        assert "Python Project" in result["github_readmes"]["python-project"]

def test_quality_reviewer_api_failure_does_not_approve():
    state = GraphState(
        job_description="Python dev",
        base_resume_md="Resume text",
        github_username="octocat",
        job_url=None,
        job_keywords=[],
        job_technologies=[],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="Generated resume",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )

    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_instance = MagicMock()
        mock_instance.with_structured_output.side_effect = Exception("Quota exceeded 429")
        mock_llm_cls.return_value = mock_instance
        
        result = quality_reviewer(state)
        assert result["reviewer_approved"] is False
        assert "Falha na API" in result["reviewer_feedback"]
        assert result["review_attempts"] == 1

def test_quality_reviewer_max_attempts():
    state = GraphState(
        job_description="",
        base_resume_md="",
        github_username="",
        job_url=None,
        job_keywords=[],
        job_technologies=[],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="Generated resume",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=2
    )
    result = quality_reviewer(state)
    assert result["reviewer_approved"] is False
    assert "Limite de tentativas" in result["reviewer_feedback"]
    assert result["review_attempts"] == 3

def test_route_after_review():
    # Caso 1: Aprovado -> Cover Letter
    s1 = {"reviewer_approved": True, "review_attempts": 1}
    assert route_after_review(s1) == "cover_letter_generator"

    # Caso 2: Reprovado com tentativas restantes -> Refaz currículo
    s2 = {"reviewer_approved": False, "review_attempts": 1}
    assert route_after_review(s2) == "resume_generator"

    # Caso 3: Reprovado mas esgotou tentativas -> Segue para Cover Letter
    s3 = {"reviewer_approved": False, "review_attempts": 2}
    assert route_after_review(s3) == "cover_letter_generator"

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
    
    result = cover_letter_generator(state)
    assert "generated_cover_letter_md" in result
    assert result["generated_cover_letter_md"] is not None
    assert len(result["generated_cover_letter_md"]) > 0
