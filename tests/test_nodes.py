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
import pytest
from langchain_core.messages import AIMessage

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
        # Encerra o loop (regenerar com feedback de falha da API não ajuda) e avisa o usuário
        assert route_after_review(result) == "cover_letter_generator"
        assert "Revisor" in result["errors"][0]

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
    
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_instance = MagicMock()
        # Formato real do Gemini 3.x: lista de blocos, às vezes com cerca ```markdown
        mock_instance.invoke.return_value = AIMessage(content=[
            {"type": "text", "text": "```markdown\nDear Hiring Manager,\nMock letter.\n```", "extras": {"signature": "x"}}
        ])
        mock_llm_cls.return_value = mock_instance
        
        result = cover_letter_generator(state)
        assert "generated_cover_letter_md" in result
        assert result["generated_cover_letter_md"] is not None
        assert result["generated_cover_letter_md"] == "Dear Hiring Manager,\nMock letter."

def _en_state(**overrides):
    state = {
        "job_description": "Full Stack Engineer - React, Node.js",
        "base_resume_md": "# Fulano\n## HABILIDADES TÉCNICAS\n- Node.js",
        "job_language": "en",
        "github_repos": [],
        "github_readmes": {},
        "generated_resume_md": "# Fulano",
    }
    state.update(overrides)
    return state

def test_resume_generator_prompt_in_job_language():
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value.invoke.return_value = AIMessage(content=[{"type": "text", "text": "# Fulano"}])
        result = resume_generator(_en_state())

        system_prompt = mock_llm_cls.return_value.invoke.call_args.args[0][0].content
        assert "TECHNICAL SKILLS" in system_prompt
        assert "| Category |" in system_prompt
        assert "TRADUZA" in system_prompt
        assert "HABILIDADES TÉCNICAS" not in system_prompt
        assert "| Categoria |" not in system_prompt
        assert result["generated_resume_md"] == "# Fulano"

def test_resume_generator_failure_propagates():
    # Antes o currículo base era devolvido e salvo como se fosse otimizado
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value.invoke.side_effect = Exception("404 model not found")
        with pytest.raises(Exception, match="404"):
            resume_generator(_en_state())

def test_cover_letter_failure_has_no_fake_letter():
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value.invoke.side_effect = Exception("429 quota")
        result = cover_letter_generator(_en_state())
        assert result["generated_cover_letter_md"] == ""
        assert "429" in result["errors"][0]

def test_llm_falls_back_on_503(monkeypatch):
    from langchain_core.runnables import RunnableLambda
    from google.genai.errors import ServerError
    from src.agents.nodes import _llm
    from src.core import config
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "modelo-reserva")

    def fake_llm(model, **_):
        def run(_):
            if model == config.GEMINI_MODEL:
                raise ServerError(503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}})
            return model
        return RunnableLambda(run)

    with patch("src.agents.nodes.ChatGoogleGenerativeAI", side_effect=fake_llm):
        assert _llm(0).invoke("oi") == "modelo-reserva"
