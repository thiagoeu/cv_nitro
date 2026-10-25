import pytest
from unittest.mock import patch, MagicMock
from src.agents.nodes import (
    _score_repository,
    _clean_readme,
    _validate_resume_deterministic,
    github_researcher,
    quality_reviewer,
    section_patcher,
    splice_markdown_section,
    cover_letter_generator
)
from src.agents.graph import route_after_review
from src.agents.state import GraphState

def test_score_repository_fork_rejected():
    repo = {"fork": True, "language": "Python", "stargazers_count": 100}
    score = _score_repository(repo, ["python"])
    assert score == -1.0

def test_score_repository_word_boundary_avoids_false_positives():
    # "c" e "go" não devem dar match em palavras como "react", "google", "algorithm"
    repo_c = {
        "fork": False,
        "language": "JavaScript",
        "description": "A react application with good algorithm",
        "topics": [],
        "stargazers_count": 0
    }
    score = _score_repository(repo_c, ["c", "go"])
    # Nenhuma palavra 'c' ou 'go' isolada na descrição
    assert score == 0.0

    # Agora com a palavra isolada 'go' e linguagem 'Go'
    repo_go = {
        "fork": False,
        "language": "Go",
        "description": "Microservice written in Go for high throughput",
        "topics": ["microservices"],
        "stargazers_count": 5
    }
    score_go = _score_repository(repo_go, ["go", "microservices"])
    # 4.0 (lang) + 2.5 (topic) + 1.5 (desc) + 1.0 (stars) = 9.0
    assert score_go >= 8.0

def test_clean_readme_removes_noise():
    raw_markdown = """
# Meu Projeto Incrível

[![Build Status](https://travis-ci.org/user/repo.svg?branch=main)](https://travis-ci.org/user/repo)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
<div align="center">Logo aqui</div>

## Sobre
Esta é uma API de alto desempenho construída com FastAPI e PostgreSQL.

## Arquitetura
A arquitetura segue os princípios de Clean Architecture com fila Celery.

## Instalação
```bash
git clone https://github.com/user/repo.git
pip install -r requirements.txt
```

## Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais detalhes.
"""
    cleaned = _clean_readme(raw_markdown, max_chars=1200)

    # Badges, tags HTML e seções de licença/instalação devem ter sido removidas
    assert "travis-ci" not in cleaned
    assert "shields.io" not in cleaned
    assert "<div" not in cleaned
    assert "Distribuído sob a licença MIT" not in cleaned
    assert "git clone" not in cleaned

    # Contexto técnico deve ser preservado
    assert "API de alto desempenho construída com FastAPI e PostgreSQL" in cleaned
    assert "Clean Architecture" in cleaned

def test_validate_resume_deterministic_detects_placeholders():
    state = {
        "github_repos": [{"url": "https://github.com/candidato/meu-repo"}],
        "github_username": "candidato",
        "job_technologies": ["Python"],
        "job_keywords": ["Backend"]
    }
    resume_with_placeholder = """
# João Silva
### Desenvolvedor Python
<Cidade, UF> | <Email>

## RESUMO PROFISSIONAL
Desenvolvedor experiente.

| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| Backend | Python, Flask |
"""
    is_valid, critical_issues, diag = _validate_resume_deterministic(resume_with_placeholder, state)
    assert is_valid is False
    assert any("marcadores de preenchimento" in issue for issue in critical_issues)
    assert diag["ats_score"] >= 50

def test_validate_resume_deterministic_detects_hallucinated_repos():
    state = {
        "github_repos": [{"url": "https://github.com/candidato/projeto-real"}],
        "github_username": "candidato",
        "job_technologies": ["Python"],
        "job_keywords": ["Backend"]
    }
    resume_with_fake_repo = """
# João Silva
### Desenvolvedor Python
São Paulo, SP | joao@email.com

## RESUMO PROFISSIONAL
Desenvolvedor experiente.

## PROJETOS EM DESTAQUE
### Projeto Fake
- **Repositório:** https://github.com/candidato/projeto-inventado

| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| Backend | Python, Flask |
"""
    is_valid, critical_issues, diag = _validate_resume_deterministic(resume_with_fake_repo, state)
    assert is_valid is False
    assert any("não consta no portfólio retornado" in issue for issue in critical_issues)

def test_validate_resume_deterministic_calculates_real_ats_score():
    state = {
        "github_repos": [{"url": "https://github.com/candidato/projeto-real"}],
        "github_username": "candidato",
        "job_technologies": ["Python", "FastAPI", "Docker"],
        "job_keywords": ["Microsserviços", "CI/CD"]
    }
    # Currículo com 100% de match de tecnologias e keywords
    full_match_resume = """
# João Silva
### Desenvolvedor Python
São Paulo, SP | joao@email.com

## RESUMO PROFISSIONAL
Especialista em microsserviços e CI/CD.

| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| Backend | Python, FastAPI, Docker |

## PROJETOS EM DESTAQUE
### Projeto Real
- **Repositório:** https://github.com/candidato/projeto-real
"""
    is_valid, critical_issues, diag = _validate_resume_deterministic(full_match_resume, state)
    assert is_valid is True
    assert critical_issues == []
    # Alta cobertura resulta em score elevado (acima de 90)
    assert diag["ats_score"] >= 90
    assert diag["tech_coverage"] == 100
    assert diag["keyword_coverage"] == 100

def test_quality_reviewer_tier1_early_rejection_without_llm():
    state = GraphState(
        job_description="Dev Python",
        base_resume_md="Resume",
        github_username="candidato",
        job_url=None,
        job_keywords=[],
        job_technologies=[],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="# João Silva\n<Cidade, UF>\n| :--- | :--- |",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0,
        strict_review=True,
        generate_cover_letter=True
    )
    # Se falhar no Tier 1, nem chama o LLM!
    with patch("src.agents.nodes._llm") as mock_llm:
        result = quality_reviewer(state)
        mock_llm.assert_not_called()
        assert result["reviewer_approved"] is False
        assert "Ajustes necessários no currículo" in result["reviewer_feedback"]

def test_quality_reviewer_economic_mode_zero_tokens():
    state = GraphState(
        job_description="Dev Python",
        base_resume_md="Resume",
        github_username="candidato",
        job_url=None,
        job_keywords=["Docker"],
        job_technologies=["Python"],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        generated_resume_md="# João Silva\nSão Paulo, SP\n| :--- | :--- |\nPython e Docker",
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0,
        strict_review=False,
        generate_cover_letter=True
    )
    with patch("src.agents.nodes._llm") as mock_llm:
        result = quality_reviewer(state)
        mock_llm.assert_not_called()
        assert result["reviewer_approved"] is True
        assert "Aprovado em modo econômico" in result["reviewer_feedback"]
        assert result["diagnostic"]["ats_score"] >= 80

def test_github_researcher_handles_rate_limit_gracefully():
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
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch("requests.get", return_value=mock_resp):
        result = github_researcher(state)
        assert result["github_repos"] == []
        assert "errors" in result
        assert any("403" in err for err in result["errors"])

def test_splice_markdown_section_exact():
    original = """# João Silva
### Desenvolvedor Senior
contato@email.com

## RESUMO PROFISSIONAL
Resumo executivo do candidato.

## HABILIDADES TÉCNICAS
- Python, Django, Flask

## EXPERIÊNCIA PROFISSIONAL
### Empresa XYZ
- Impacto relevante em produção.
"""
    new_skills = """## HABILIDADES TÉCNICAS
| Categoria | Tecnologias & Conceitos |
| :--- | :--- |
| Backend | Python, FastAPI, Docker |
"""
    updated = splice_markdown_section(original, "HABILIDADES TÉCNICAS", new_skills)
    assert "| Categoria | Tecnologias & Conceitos |" in updated
    assert "- Python, Django, Flask" not in updated
    # Garante que as outras seções foram mantidas intactas
    assert "# João Silva" in updated
    assert "## RESUMO PROFISSIONAL" in updated
    assert "## EXPERIÊNCIA PROFISSIONAL" in updated

def test_splice_markdown_section_case_insensitive_and_tolerance():
    original = """# Maria Souza
## Summary
Software engineer with cloud experience.

## Technical Skills
| Category | Stack |
| :--- | :--- |
| Cloud | AWS |

## Education
B.S. Computer Science
"""
    new_skills = """| Category | Stack |
| :--- | :--- |
| Cloud | AWS, GCP, Terraform |
"""
    # Procura com título em minúsculas e sem cabeçalho no novo conteúdo
    updated = splice_markdown_section(original, "technical skills", new_skills)
    assert "Terraform" in updated
    assert "## Education" in updated
    assert "B.S. Computer Science" in updated

def test_splice_markdown_section_nonexistent_section_returns_original():
    original = "# Currículo\n## Seção A\nTexto A"
    updated = splice_markdown_section(original, "Seção Inexistente", "## Nova Seção\nConteúdo")
    assert updated == original

def test_section_patcher_node():
    state = {
        "generated_resume_md": "# Dev\n## HABILIDADES TÉCNICAS\n- Lista antiga",
        "patch_section": "HABILIDADES TÉCNICAS",
        "patch_instruction": "Substitua a lista por uma tabela de 2 colunas com Python e Docker.",
        "job_language": "pt"
    }

    mock_response = MagicMock()
    mock_response.text = "## HABILIDADES TÉCNICAS\n| Categoria | Stack |\n| :--- | :--- |\n| Backend | Python, Docker |"

    with patch("src.agents.nodes._llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_response
        res = section_patcher(state)
        assert "| Backend | Python, Docker |" in res["generated_resume_md"]
        assert "- Lista antiga" not in res["generated_resume_md"]
        assert "# Dev" in res["generated_resume_md"]

def test_route_after_review_minor_vs_major():
    # 1. Falha Minor com seção identificada -> deve ir para section_patcher
    state_minor = {
        "reviewer_approved": False,
        "review_attempts": 1,
        "review_severity": "minor",
        "patch_section": "HABILIDADES TÉCNICAS"
    }
    assert route_after_review(state_minor) == "section_patcher"

    # 2. Falha Major -> deve ir para resume_generator (reescrita completa)
    state_major = {
        "reviewer_approved": False,
        "review_attempts": 1,
        "review_severity": "major",
        "patch_section": None
    }
    assert route_after_review(state_major) == "resume_generator"

    # 3. Falha Minor mas sem seção alvo identificada -> fallback seguro para resume_generator
    state_minor_no_section = {
        "reviewer_approved": False,
        "review_attempts": 1,
        "review_severity": "minor",
        "patch_section": None
    }
    assert route_after_review(state_minor_no_section) == "resume_generator"

