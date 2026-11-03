import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

# Grafias do mesmo item (versões, siglas, traduções): valem nos dois sentidos.
ALIASES: List[Set[str]] = [
    {"html", "html5"},
    {"css", "css3"},
    {"javascript", "js", "es6", "es2015", "ecmascript"},
    {"typescript", "ts"},
    {"postgresql", "postgres"},
    {"sql server", "mssql"},
    {"node.js", "nodejs", "node"},
    {"go", "golang"},
    {"apis rest", "api rest", "rest api", "rest apis", "restful", "restful api", "restful apis", "rest"},
    {"inteligencia artificial generativa", "ia generativa", "generative ai", "genai"},
    {"rag", "retrieval-augmented generation"},
    {"llm", "llms"},
    {"machine learning", "ml", "aprendizado de maquina"},
    {"mensageria", "message broker"},
    {"clean code", "codigo limpo"},
    {"clean architecture", "arquitetura limpa"},
    {"solid", "principios solid"},
]

# Genérico -> itens específicos que o comprovam. Vale só nesse sentido:
# MySQL prova SQL, mas SQL não prova MySQL e MySQL não prova PostgreSQL (irmãos).
FAMILIES: Dict[str, Set[str]] = {
    "sql": {"postgresql", "mysql", "sqlite", "mariadb", "sql server", "tsql", "plsql"},
    "inteligencia artificial generativa": {"rag", "llm", "ollama"},
    "machine learning": {"scikit-learn"},
    "docker": {"docker compose"},
    "git": {"github", "gitlab", "github actions"},
    "mensageria": {"rabbitmq", "kafka", "amqp"},
    "node.js": {"nestjs", "express"},
    "testes automatizados": {"testes unitarios", "testes de integracao", "pytest", "jest"},
}

# Termos que colidem com palavras comuns ("R&D", "go-live", "the rest of"):
# exigem a grafia técnica e não podem estar colados a '&' ou '-'.
AMBIGUOUS_TERMS: Dict[str, str] = {"c": "C", "r": "R", "go": "Go", "rest": "REST", "ts": "TS", "ml": "ML"}


def _strip_accents(text: str) -> str:
    """Remove acentos para comparação normalizada."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _clean_term(term: str) -> str:
    """Normaliza o termo para minúsculas e sem acentos."""
    return _strip_accents((term or "").lower().strip())


def _aliases(term_clean: str) -> Set[str]:
    for group in ALIASES:
        if term_clean in group:
            return group
    return {term_clean}


def _accepted_forms(term_clean: str) -> Set[str]:
    """Sinônimos do termo e, se ele for genérico, os itens específicos da família (nunca os irmãos)."""
    forms = set(_aliases(term_clean))
    for key in list(forms):
        for member in FAMILIES.get(key, ()):
            forms |= _aliases(member)
    return forms


@lru_cache(maxsize=None)
def _form_regex(form: str) -> re.Pattern:
    """Fronteira de palavra que também separa C de C++/C#; termos ambíguos diferenciam maiúsculas."""
    if form in AMBIGUOUS_TERMS:
        return re.compile(rf"(?<![a-zA-Z0-9&-]){re.escape(AMBIGUOUS_TERMS[form])}(?![a-zA-Z0-9+#&-])")
    return re.compile(rf"(?<![a-zA-Z0-9]){re.escape(form)}(?![a-zA-Z0-9+#])", re.IGNORECASE)


def matches_technology(required_tech: str, text: str) -> bool:
    """
    Verifica se uma tecnologia exigida está presente no texto informado,
    considerando sinônimos e, para requisitos genéricos, os itens específicos da família.
    """
    if not required_tech or not text:
        return False
    plain = _strip_accents(text)
    return any(_form_regex(form).search(plain) for form in _accepted_forms(_clean_term(required_tech)))


def candidate_evidence(
    base_resume: str = "",
    github_repos: Optional[List[Dict[str, Any]]] = None,
    readmes: Optional[Dict[str, str]] = None,
) -> str:
    """Base de evidências única do candidato: currículo base, repositórios e extratos dos READMEs."""
    parts = [base_resume or ""]
    for r in github_repos or []:
        parts += [r.get("name") or "", r.get("description") or "", r.get("language") or ""]
    parts += list((readmes or {}).values())
    return "\n".join(parts)


def classify_competencies(
    job_technologies: List[str],
    base_resume: str = "",
    github_repos: Optional[List[Dict[str, Any]]] = None,
    readmes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Separa os requisitos da vaga em tecnologias comprovadas (diretas ou equivalentes)
    e pendências técnicas reais (gaps) que o candidato não possui no histórico.
    """
    candidate_corpus = candidate_evidence(base_resume, github_repos, readmes)

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
