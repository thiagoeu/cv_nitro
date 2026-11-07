"""Formatadores compartilhados de contexto do GraphState para os nós do pipeline."""
from src.core import competency_matcher as competency_matcher_core


def job_context(state: dict) -> str:
    """Resumo da vaga + termos ATS no lugar do texto colado: corta boilerplate (benefícios, institucional) de cada chamada seguinte."""
    summary = state.get("job_summary")
    if not summary:
        return state.get("job_description", "")
    terms = ", ".join(dict.fromkeys((state.get("job_technologies") or []) + (state.get("job_keywords") or [])))
    return f"{summary}\n\nPalavras-chave ATS: {terms}"


def portfolio_context(state: dict, readme_chars: int = 1200) -> str:
    """Formata os repositórios curados e extratos dos READMEs para consumo pelos prompts."""
    context = ""
    readmes = state.get("github_readmes", {})
    for repo in state.get("github_repos", []):
        name = repo["name"]
        cleaned_content = readmes.get(name, "")[:readme_chars]
        context += (
            f"\n### Repositório: {name}\nURL: {repo.get('url', '')}\nLinguagem: {repo.get('language', '')}\n"
            f"Descrição: {repo.get('description', '')}\nREADME (extrato técnico):\n{cleaned_content}\n"
        )
    return context


def format_repos_summary(repos: list, max_repos: int = 3) -> str:
    """Gera lista enxuta de repositórios em destaque para a carta de apresentação."""
    project_items = []
    for r in (repos or [])[:max_repos]:
        name = r.get("name")
        if not name:
            continue
        lang = r.get("language") or "Multi-stack"
        desc = (r.get("description") or "").strip()
        if desc:
            desc_short = desc[:110] + ("..." if len(desc) > 110 else "")
            project_items.append(f"- **{name}** ({lang}): {desc_short}")
        else:
            project_items.append(f"- **{name}** ({lang})")
    return "\n".join(project_items) if project_items else "Nenhum repositório específico."


def resolve_verified_and_gaps(state: dict) -> tuple[list, list]:
    """Obtém tecnologias comprovadas e lacunas do estado, com fallback determinístico caso ausentes."""
    verified_techs = state.get("verified_technologies")
    gaps = state.get("unmatched_gaps")
    if verified_techs is None or gaps is None:
        classified = competency_matcher_core.classify_competencies(
            state.get("job_technologies", []),
            state.get("base_resume_md", ""),
            state.get("github_repos", []) or state.get("raw_github_repos", []) or [],
            state.get("github_readmes"),
        )
        verified_techs = classified["verified_technologies"]
        gaps = classified["unmatched_gaps"]
    return verified_techs, gaps

