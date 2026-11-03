import pytest
from src.core import competency_matcher


def test_matches_technology_direct():
    text = "Desenvolvedor com experiência em Python, FastAPI e Docker."
    assert competency_matcher.matches_technology("Python", text) is True
    assert competency_matcher.matches_technology("Docker", text) is True
    assert competency_matcher.matches_technology("Java", text) is False


def test_matches_technology_version_and_variants():
    # HTML5 atende a HTML
    assert competency_matcher.matches_technology("HTML", "Desenvolvimento com HTML5 e CSS3.") is True
    assert competency_matcher.matches_technology("CSS", "Desenvolvimento com HTML5 e CSS3.") is True
    # JavaScript atende a JS / ES6
    assert competency_matcher.matches_technology("JavaScript", "Código escrito em ES6 e TypeScript.") is True


def test_matches_technology_relational_sql_dialects():
    # PostgreSQL ou MySQL atendem a SQL
    text = "Bancos de dados relacionais com PostgreSQL e TypeORM."
    assert competency_matcher.matches_technology("SQL", text) is True
    assert competency_matcher.matches_technology("PostgreSQL", text) is True
    assert competency_matcher.matches_technology("MySQL", "Instalação do MySQL Server") is True


def test_matches_technology_rest_and_ai_variants():
    text = "Criação de RESTful APIs com NestJS e aplicação de IA Generativa com RAG e Ollama."
    assert competency_matcher.matches_technology("APIs REST", text) is True
    assert competency_matcher.matches_technology("Inteligência Artificial Generativa", text) is True
    assert competency_matcher.matches_technology("RabbitMQ", "Mensageria com RabbitMQ (Topic Exchanges)") is True


def test_matches_technology_does_not_false_positive_unrelated_stacks():
    text = "Especialista em Node.js, NestJS, TypeScript, React e PostgreSQL."
    assert competency_matcher.matches_technology("C#", text) is False
    assert competency_matcher.matches_technology(".NET Framework", text) is False
    assert competency_matcher.matches_technology("ASP.NET MVC", text) is False
    assert competency_matcher.matches_technology("Angular", text) is False
    assert competency_matcher.matches_technology("Java", text) is False


def test_classify_competencies():
    job_reqs = [
        "C#",
        ".NET Framework",
        "SQL",
        "HTML",
        "CSS",
        "JavaScript",
        "APIs REST",
        "Inteligência Artificial Generativa",
        "Angular",
    ]
    base_cv = """
    Desenvolvedor Full Stack com Node.js, TypeScript e React 19.
    Construção de RESTful APIs, bancos PostgreSQL e interfaces em HTML5 e CSS3.
    Experiência em IA Generativa (RAG e Ollama).
    """
    repos = [{"name": "portifolio", "language": "JavaScript", "description": "Web portfolio"}]

    res = competency_matcher.classify_competencies(job_reqs, base_cv, repos)

    # Tecnologias que o candidato possui de fato (diretas ou equivalentes)
    assert "SQL" in res["verified_technologies"]
    assert "HTML" in res["verified_technologies"]
    assert "CSS" in res["verified_technologies"]
    assert "JavaScript" in res["verified_technologies"]
    assert "APIs REST" in res["verified_technologies"]
    assert "Inteligência Artificial Generativa" in res["verified_technologies"]

    # Pendências técnicas reais (Gaps que o candidato NÃO possui)
    assert "C#" in res["unmatched_gaps"]
    assert ".NET Framework" in res["unmatched_gaps"]
    assert "Angular" in res["unmatched_gaps"]

    # Taxa calculada corretamente (6 de 9 = 67%)
    assert res["match_rate"] == 67

