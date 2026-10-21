import pytest
from unittest.mock import patch, MagicMock
from langgraph.graph import END
from src.agents.state import GraphState
from src.agents.nodes import quality_reviewer, ReviewResult
from src.agents.graph import route_after_review, build_graph

def test_route_after_review_with_cover_letter_disabled():
    # Caso aprovado com generate_cover_letter=False -> Deve retornar END
    state = {
        "reviewer_approved": True,
        "review_attempts": 1,
        "generate_cover_letter": False
    }
    assert route_after_review(state) == END

    # Caso esgotou tentativas com generate_cover_letter=False -> Deve retornar END
    state_max = {
        "reviewer_approved": False,
        "review_attempts": 2,
        "generate_cover_letter": False
    }
    assert route_after_review(state_max) == END

    # Caso padrão (generate_cover_letter=True) -> Deve ir para cover_letter_generator
    state_enabled = {
        "reviewer_approved": True,
        "review_attempts": 1,
        "generate_cover_letter": True
    }
    assert route_after_review(state_enabled) == "cover_letter_generator"

def test_quality_reviewer_economic_mode():
    # Modo econômico (strict_review=False) não deve chamar a LLM e deve aprovar com diagnóstico
    state = GraphState(
        job_description="Vaga Python e FastAPI com Docker",
        base_resume_md="# João Silva\nDesenvolvedor",
        github_username="joao",
        job_url=None,
        job_keywords=["FastAPI", "Docker", "REST API"],
        job_technologies=["Python", "Docker"],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="# João Silva\nExperiência em Python, Docker e FastAPI em microsserviços.",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0,
        strict_review=False,
        generate_cover_letter=False
    )

    result = quality_reviewer(state)
    assert result["reviewer_approved"] is True
    assert "econômico" in result["reviewer_feedback"]
    assert "diagnostic" in result
    diag = result["diagnostic"]
    assert diag["ats_score"] >= 70
    assert "Python" in diag["matched_keywords"] or "Docker" in diag["matched_keywords"]
    assert len(diag["applied_changes"]) > 0

def test_quality_reviewer_strict_mode_with_diagnostic():
    state = GraphState(
        job_description="Desenvolvedor Python Pleno",
        base_resume_md="# Maria Souza\nEngenheira de Software",
        github_username="maria",
        job_url=None,
        job_keywords=["Python", "SQL", "Git"],
        job_technologies=["Python", "PostgreSQL"],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="# Maria Souza\nDesenvolvedora Python com PostgreSQL e Git.",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0,
        strict_review=True,
        generate_cover_letter=True
    )

    mock_review = ReviewResult(
        approved=True,
        feedback="Currículo impecável e alinhado aos padrões ATS.",
        ats_score=92,
        applied_changes=[
            "Tabela de habilidades organizada em 2 colunas",
            "Bullets com métricas e verbos de ação",
            "Inclusão de palavras-chave da vaga"
        ]
    )

    from langchain_core.runnables import RunnableLambda

    with patch("src.agents.nodes._llm") as mock_llm_fn:
        mock_instance = MagicMock()
        mock_instance.with_structured_output.return_value = RunnableLambda(lambda x: mock_review)
        mock_llm_fn.return_value = mock_instance

        result = quality_reviewer(state)
        assert result["reviewer_approved"] is True
        assert "diagnostic" in result
        assert result["diagnostic"]["ats_score"] == 92
        assert len(result["diagnostic"]["applied_changes"]) == 3
        assert "Python" in result["diagnostic"]["matched_keywords"]

def test_build_graph_compiles_successfully():
    graph = build_graph()
    assert graph is not None
