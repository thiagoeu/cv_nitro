from unittest.mock import patch, MagicMock
from src.agents.nodes import (
    job_analyzer,
    github_fetcher,
    relevance_ranker,
    resume_generator,
    quality_reviewer,
    cover_letter_generator
)
from src.agents.graph import route_after_review
from src.agents.state import GraphState
import os
import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Dummy fallback API key for testing structural parsing
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "dummy")

def test_github_fetcher_invalid_username():
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
    with patch("requests.get") as mock_get:
        result = github_fetcher(state)
        assert not mock_get.called
    assert result["raw_github_repos"] == []
    assert "inválido" in result["errors"][0]

def test_github_fetcher_and_ranker_with_mock():
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
        result = relevance_ranker({**state, **github_fetcher(state)})

        # Valida que timeout foi repassado nas chamadas requests
        assert mock_get.call_count == 2
        for call_args in mock_get.call_args_list:
            assert "timeout" in call_args.kwargs
            assert call_args.kwargs["timeout"] == (5.0, 10.0)
        assert "per_page=100" in mock_get.call_args_list[0].args[0]
        assert mock_get.call_args_list[0].kwargs["headers"]["Accept"] == "application/vnd.github+json"
            
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
        assert "PRIMEIRA PESSOA" in system_prompt
        assert result["generated_resume_md"] == "# Fulano"

def test_resume_generator_uses_job_summary():
    state = _en_state(job_description="Join Our Team! Great Place to Work... React role", job_summary="Senior React engineer",
                      job_technologies=["React"], job_keywords=["ownership"])
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_cls.return_value.invoke.return_value = AIMessage(content="# Fulano")
        resume_generator(state)
        # Mensagens: [0] SystemMessage (Regras ATS), [1] HumanMessage (Currículo Base), [2] HumanMessage (Vaga)
        user_messages = [m.content for m in mock_llm_cls.return_value.invoke.call_args.args[0] if isinstance(m, HumanMessage)]
        user_prompt = " ".join(user_messages)
        assert "Senior React engineer" in user_prompt
        assert "React, ownership" in user_prompt
        assert "Great Place to Work" not in user_prompt

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

def test_llm_falls_back_to_groq_on_quota(monkeypatch):
    from langchain_core.runnables import RunnableLambda
    from src.agents.nodes import _llm
    from src.core import config
    monkeypatch.setattr(config, "GROQ_API_KEY", "gsk-teste")

    def quota(_):
        raise Exception("429 RESOURCE_EXHAUSTED")

    with patch("src.agents.nodes.ChatGoogleGenerativeAI", return_value=RunnableLambda(quota)), \
         patch("src.agents.nodes.ChatGroq", return_value=RunnableLambda(lambda _: "groq")):
        assert _llm(0).invoke("oi") == "groq"

def test_github_fetcher_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"name": "repo1", "fork": False},
        {"name": "repo2", "fork": True}
    ]
    with patch("requests.get", return_value=mock_resp):
        res = github_fetcher({"github_username": "octocat"})
        assert len(res["raw_github_repos"]) == 2
        assert res["raw_github_repos"][0]["name"] == "repo1"

def test_relevance_ranker_deterministic_ordering():
    raw_repos = [
        {
            "name": "forked-repo",
            "fork": True,
            "language": "Python",
            "description": "A fork",
            "stargazers_count": 100
        },
        {
            "name": "python-fastapi-service",
            "fork": False,
            "language": "Python",
            "topics": ["fastapi", "backend"],
            "description": "A high-performance FastAPI microservice",
            "stargazers_count": 10,
            "updated_at": "2026-01-01T00:00:00Z"
        },
        {
            "name": "ruby-app",
            "fork": False,
            "language": "Ruby",
            "topics": ["rails"],
            "description": "Rails ecommerce application",
            "stargazers_count": 5,
            "updated_at": "2026-01-02T00:00:00Z"
        },
        {
            "name": "python-script",
            "fork": False,
            "language": "Python",
            "topics": [],
            "description": "Small utility script",
            "stargazers_count": 0,
            "updated_at": "2025-01-01T00:00:00Z"
        }
    ]

    state = {
        "github_username": "octocat",
        "job_technologies": ["Python", "FastAPI"],
        "raw_github_repos": raw_repos
    }

    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 404

    with patch("requests.get", return_value=mock_readme_resp):
        res = relevance_ranker(state)
        selected = res["github_repos"]
        assert len(selected) <= 3
        # python-fastapi-service deve vir em 1º lugar absoluto por bater language + topic + description
        assert selected[0]["name"] == "python-fastapi-service"
        assert selected[0]["relevance_score"] > selected[1]["relevance_score"]
        # Forked repo não deve ser o primeiro
        assert "forked-repo" not in [s["name"] for s in selected]

def test_resume_generator_single_call_with_readmes_in_prompt():
    state = _en_state(
        github_repos=[{"name": "nitro-app", "url": "https://github.com/test/nitro-app", "language": "Python", "description": "Nitro App", "relevance_score": 8.0}],
        github_readmes={"nitro-app": "## Arquitetura\nMicrosserviço de alta concorrência em FastAPI."}
    )
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="# Currículo")

    with patch("src.agents.nodes._llm", return_value=mock_llm):
        result = resume_generator(state)

    assert result["generated_resume_md"] == "# Currículo"
    assert mock_llm.invoke.call_count == 1
    assert not mock_llm.bind_tools.called
    prompt_text = " ".join(m.content for m in mock_llm.invoke.call_args[0][0] if isinstance(m, HumanMessage))
    assert "Microsserviço de alta concorrência em FastAPI" in prompt_text
    assert "https://github.com/test/nitro-app" in prompt_text

def test_llm_clients_use_bounded_timeout(monkeypatch):
    from src.agents.nodes import _llm
    from src.core import config
    monkeypatch.setattr(config, "GEMINI_FALLBACK_MODEL", "modelo-reserva")
    monkeypatch.setattr(config, "GROQ_API_KEY", "gsk-teste")
    with patch("src.agents.nodes.ChatGoogleGenerativeAI") as gemini, \
         patch("src.agents.nodes.ChatGroq") as groq:
        _llm(0)
    calls = gemini.call_args_list + groq.call_args_list
    assert len(calls) == 3
    assert all(c.kwargs["timeout"] == 120 and c.kwargs["max_retries"] == 1 for c in calls)

def test_github_fetcher_reuses_cached_repos():
    cached = [{"name": "repo", "html_url": "https://github.com/octocat/repo"}]
    with patch("requests.get") as mock_get:
        res = github_fetcher({"github_username": "octocat", "raw_github_repos": cached})
    assert not mock_get.called
    assert res["raw_github_repos"] == cached
    assert "agent_trace" in res
    assert res["agent_trace"][0]["agent"] == "github_fetcher"


def test_validate_resume_deterministic_semantic_equivalences_and_factual_lock():
    from src.agents.nodes import _validate_resume_deterministic

    state = {
        "job_technologies": ["HTML", "SQL", "APIs REST", "Inteligência Artificial Generativa", "C#"],
        "job_keywords": ["Git"],
        "base_resume_md": "Dev Node.js e React",
        "github_repos": [],
        "unmatched_gaps": ["C#"],
    }

    # Caso 1: Currículo contém as equivalências (HTML5, PostgreSQL, RESTful APIs, IA Generativa), mas NÃO tem C#
    cv_valid = """
    # Candidato
    ## Habilidades
    | Categoria | Tecnologias |
    | :--- | :--- |
    | Web & Backend | HTML5, PostgreSQL, RESTful APIs, IA Generativa, Git |
    """
    is_valid, critical_issues, diag = _validate_resume_deterministic(cv_valid, state)
    assert is_valid is True
    assert "HTML" in diag["matched_keywords"]
    assert "SQL" in diag["matched_keywords"]
    assert "APIs REST" in diag["matched_keywords"]
    assert "Inteligência Artificial Generativa" in diag["matched_keywords"]
    assert "C#" in diag["missing_keywords"]

    # Caso 2: Currículo inventa C# no texto violando a trava factual
    cv_invented = """
    # Candidato
    ## Habilidades
    | Categoria | Tecnologias |
    | :--- | :--- |
    | Web & Backend | HTML5, PostgreSQL, C# |
    """
    is_valid_inv, critical_issues_inv, _ = _validate_resume_deterministic(cv_invented, state)
    assert is_valid_inv is False
    assert any("Violação de trava factual" in issue for issue in critical_issues_inv)


def test_validate_resume_deterministic_gap_never_matched_and_score_capped():
    from src.agents.nodes import _validate_resume_deterministic

    state = {
        "job_technologies": ["Java", "Git", "Estrutura de Dados", "Algoritmos"],
        "job_keywords": ["código limpo", "revisão de código"],
        "base_resume_md": "Desenvolvedor Full Stack Node.js, React e Git",
        "github_repos": [],
        "unmatched_gaps": ["Java"],
        "verified_technologies": ["Git", "Estrutura de Dados", "Algoritmos"],
    }

    # Mesmo que o texto mencione 'Java' (ex.: no resumo ou aspiração), Java NUNCA pode ser matched_keyword
    cv_with_aspirational_mention = """
    # Thiago Araújo
    ### Desenvolvedor Full Stack
    ## RESUMO
    Desenvolvedor Full Stack. Busco aprender Java rapidamente.
    ## HABILIDADES TÉCNICAS
    | Categoria | Tecnologias |
    | :--- | :--- |
    | Geral | Git, Estrutura de Dados, Algoritmos, código limpo, revisão de código |
    """

    is_valid, critical_issues, diag = _validate_resume_deterministic(cv_with_aspirational_mention, state)
    # Java NÃO pode constar em matched_keywords
    assert "Java" not in diag["matched_keywords"]
    # Java DEVE constar obrigatoriamente em missing_keywords
    assert "Java" in diag["missing_keywords"]
    # O Score ATS JAMAIS pode ser 100% quando há pendência técnica na stack da vaga
    assert diag["ats_score"] < 80
