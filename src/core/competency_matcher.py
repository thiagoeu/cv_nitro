import re
import unicodedata
from typing import Any, Dict, List, Optional, Set

# Dicionário canônico de equivalências de mercado.
# A chave representa o conceito canônico e o conjunto contém variantes legítimas
# (versões, siglas, dialetos ou subconjuntos diretos).
CANONICAL_EQUIVALENCES: Dict[str, Set[str]] = {
    "html": {"html", "html5"},
    "css": {"css", "css3"},
    "javascript": {"javascript", "js", "es6", "es2015", "ecmascript"},
    "typescript": {"typescript", "ts"},
    "sql": {
        "sql",
        "postgresql",
        "postgres",
        "mysql",
        "sqlite",
        "mariadb",
        "sql server",
        "mssql",
        "tsql",
        "plsql",
    },
    "apis rest": {
        "apis rest",
        "api rest",
        "rest api",
        "rest apis",
        "restful",
        "restful apis",
        "restful api",
        "rest",
    },
    "inteligencia artificial generativa": {
        "inteligencia artificial generativa",
        "ia generativa",
        "generative ai",
        "genai",
        "rag",
        "retrieval-augmented generation",
        "llm",
        "llms",
        "ollama",
    },
    "machine learning": {
        "machine learning",
        "ml",
        "aprendizado de maquina",
        "scikit-learn",
    },
    "docker": {"docker", "docker compose", "container", "containerizacao", "conteinerizacao"},
    "git": {"git", "github", "gitlab", "github actions"},
    "rabbitmq": {"rabbitmq", "mensageria", "message broker", "amqp"},
    "node.js": {"node.js", "nodejs", "node", "nestjs", "express"},
    "clean code": {"clean code", "codigo limpo", "boas praticas"},
    "clean architecture": {"clean architecture", "arquitetura limpa"},
    "solid": {"solid", "principios solid"},
    "testes automatizados": {
        "testes automatizados",
        "testes unitarios",
        "testes de integracao",
        "pytest",
        "jest",
    },
}


def _strip_accents(text: str) -> str:
    """Remove acentos para comparação normalizada."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _clean_term(term: str) -> str:
    """Normaliza o termo para minúsculas e sem acentos."""
    return _strip_accents((term or "").lower().strip())


def _find_canonical_key(term_clean: str) -> Optional[str]:
    """Identifica se o termo pertence a um grupo canônico de equivalências."""
    if term_clean in CANONICAL_EQUIVALENCES:
        return term_clean
    for canon_key, variants in CANONICAL_EQUIVALENCES.items():
        if term_clean in variants:
            return canon_key
    return None


def _build_term_regex(term_clean: str) -> str:
    """
    Constrói regex com limite de palavras adaptada para termos técnicos
    com símbolos (+, #, ., -), preservando distinções como C vs C++ vs C#.
    """
    escaped = re.escape(term_clean)
    # Se terminar com dígito (ex: html5), permite match sem considerar \b após o dígito
    return rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"


def matches_technology(required_tech: str, text: str) -> bool:
    """
    Verifica se uma tecnologia exigida está presente no texto informado,
    considerando correspondência direta e equivalências canônicas legítimas.
    """
    if not required_tech or not text:
        return False

    req_clean = _clean_term(required_tech)
    text_clean = _clean_term(text)

    # 1. Correspondência direta do termo original
    direct_pattern = _build_term_regex(req_clean)
    if re.search(direct_pattern, text_clean):
        return True

    # 2. Correspondência por grupo de equivalências canônicas
    canon_key = _find_canonical_key(req_clean)
    if canon_key:
        variants = CANONICAL_EQUIVALENCES[canon_key]
        for variant in variants:
            var_clean = _clean_term(variant)
            pattern = _build_term_regex(var_clean)
            if re.search(pattern, text_clean):
                return True

    return False


def classify_competencies(
    job_technologies: List[str],
    base_resume: str = "",
    github_repos: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Separa os requisitos da vaga em tecnologias comprovadas (diretas ou equivalentes)
    e pendências técnicas reais (gaps) que o candidato não possui no histórico.
    """
    github_repos = github_repos or []
    repo_parts = []
    for r in github_repos:
        name = r.get("name") or ""
        desc = r.get("description") or ""
        lang = r.get("language") or ""
        repo_parts.extend([name, desc, lang])

    candidate_corpus = (base_resume or "") + " " + " ".join(repo_parts)

    verified: List[str] = []
    gaps: List[str] = []
    seen = set()

    for tech in job_technologies:
        t_clean = (tech or "").strip()
        if not t_clean or t_clean.lower() in seen:
            continue
        seen.add(t_clean.lower())

        if matches_technology(t_clean, candidate_corpus):
            verified.append(t_clean)
        else:
            gaps.append(t_clean)

    total = max(len(seen), 1)
    match_rate = round((len(verified) / total) * 100)

    return {
        "verified_technologies": verified,
        "unmatched_gaps": gaps,
        "match_rate": match_rate,
        "total_required": len(seen),
    }

