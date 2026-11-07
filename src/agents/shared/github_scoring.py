"""Utilitários determinísticos de pontuação de repositórios GitHub e higienização de READMEs."""
import re
from typing import List
from src.core import config
from src.core import competency_matcher as competency_matcher_core

GITHUB_TIMEOUT = (5.0, 10.0)


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = config.GITHUB_TOKEN
    if token and "your_github_token_here" not in token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _score_repository_with_matches(repo: dict, target_technologies: List[str], job_title: str = "") -> tuple[float, set]:
    """
    Pontua a relevância de um repositório para a vaga alvo de forma determinística (0 tokens de LLM).
    Considera forks (penalizados/ignorados), nome do repositório, linguagem principal,
    topics/tags (normalizando hífens e equivalências), descrição e tecnologias em destaque no título da vaga.
    Retorna (score, matched_technologies_set).
    """
    if repo.get("fork", False):
        return -1.0, set()

    score = 0.0
    matched_techs = set()
    tech_list = [t.strip() for t in target_technologies if t and t.strip()]
    if not tech_list:
        return 1.0, set()

    name = (repo.get("name") or "").lower()
    name_norm = name.replace("-", " ").replace("_", " ")
    desc = (repo.get("description") or "").lower()
    desc_norm = desc.replace("-", " ").replace("_", " ")
    repo_lang = (repo.get("language") or "").strip().lower()
    raw_topics = [str(t).strip().lower() for t in (repo.get("topics", []) or [])]
    topics_norm = [t.replace("-", " ").replace("_", " ") for t in raw_topics]

    title_lower = (job_title or "").lower()

    for tech in tech_list:
        t_clean = tech.lower()
        t_norm = t_clean.replace("-", " ").replace("_", " ")
        is_title_tech = (t_norm in title_lower or t_clean in title_lower) if title_lower else False
        tech_matched = False

        # 1. Nome do repositório (+4.5)
        name_pattern = rf"(?<!\w){re.escape(t_norm)}(?!\w)"
        if re.search(name_pattern, name_norm) or re.search(rf"(?<!\w){re.escape(t_clean)}(?!\w)", name) or competency_matcher_core.matches_technology(tech, name):
            score += 4.5
            tech_matched = True

        # 2. Correspondência em topics/tags (+3.5 por tópico coincidente)
        for t_raw, t_n in zip(raw_topics, topics_norm):
            if t_raw == t_clean or t_n == t_norm or competency_matcher_core.matches_technology(tech, t_raw):
                score += 3.5
                tech_matched = True
                break

        # 3. Correspondência na linguagem principal (+4.0)
        if repo_lang and (repo_lang == t_clean or repo_lang == t_norm or competency_matcher_core.matches_technology(tech, repo_lang)):
            score += 4.0
            tech_matched = True

        # 4. Correspondência na descrição com word boundaries (+2.0 por termo)
        desc_pattern = rf"(?<!\w){re.escape(t_norm)}(?!\w)"
        if re.search(desc_pattern, desc_norm) or re.search(rf"(?<!\w){re.escape(t_clean)}(?!\w)", desc) or competency_matcher_core.matches_technology(tech, desc):
            score += 2.0
            tech_matched = True

        if tech_matched:
            matched_techs.add(tech)
            # Super bônus (+6.0): tecnologia central destacada no cargo / título da vaga
            if is_title_tech:
                score += 6.0

    # 5. Bônus por popularidade (estrelas)
    stars = int(repo.get("stargazers_count") or 0)
    if stars > 0:
        score += min(2.0, stars * 0.2)

    return score, matched_techs


def _score_repository(repo: dict, target_technologies: List[str], job_title: str = "") -> float:
    score, _ = _score_repository_with_matches(repo, target_technologies, job_title)
    return score


def _clean_readme(raw_markdown: str, max_chars: int = 1200) -> str:
    """
    Higieniza o conteúdo de um README removendo ruídos irrelevantes (badges, tags HTML,
    links de licença, comandos de instalação) e preservando a arquitetura e funcionalidades.
    """
    if not raw_markdown:
        return ""

    text = raw_markdown

    # Remove tags HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove badges em Markdown: [![...](...)](...) ou ![...](...)
    text = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Transforma links normais [Texto](URL) apenas no texto do link
    text = re.sub(r"\[(.*?)\]\(https?://[^\s)]+\)", r"\1", text)

    # Remove seções triviais de Licença, Contribuição ou Instalação padrão
    section_pattern = r"(?im)^##+\s+(?:licen[çc]a|license|contributing|contribui[çc][ãa]o|como rodar|instala[çc][ãa]o|installation)[\s\S]*?(?=(?:^##+\s+)|\Z)"
    text = re.sub(section_pattern, "", text)

    # Normaliza múltiplos espaços e quebras de linha consecutivas
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()

    if len(text) <= max_chars:
        return text

    # Trunca no limite respeitando o último parágrafo ou ponto final
    truncated = text[:max_chars]
    last_break = max(truncated.rfind("\n"), truncated.rfind(". "))
    if last_break > max_chars * 0.6:
        return truncated[:last_break].strip() + "\n..."
    return truncated.strip() + "..."

