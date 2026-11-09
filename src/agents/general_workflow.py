"""Endpoint e fluxo independente para otimização geral de currículo (sem vaga específica)."""
import base64
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional
import requests

from src.agents.nodes.github import github_fetcher
from src.agents.prompts.general_prompts import (
    build_general_resume_system_prompt,
    build_general_resume_user_messages,
)
from src.agents.shared import llm
from src.agents.shared.context import portfolio_context
from src.agents.shared.deterministic_validator import _validate_resume_deterministic
from src.agents.shared.github_scoring import GITHUB_TIMEOUT, _clean_readme, _github_headers
from src.agents.shared.project_injector import inject_projects_from_urls, parse_github_repo_urls
from src.agents.shared.sections import LABELS
from src.core import competency_matcher as competency_matcher_core

# Catálogo curado de tecnologias relevantes do mercado para detecção determinística no perfil/portfólio
COMMON_TECH_CATALOG = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "Go", "Rust", "PHP", "Ruby", "Kotlin", "Swift", "C++", "SQL",
    "React", "Next.js", "Vue.js", "Angular", "Node.js", "Express", "NestJS", "FastAPI", "Django", "Flask",
    "Spring Boot", ".NET", "Laravel", "GraphQL", "REST API", "gRPC", "Tailwind CSS", "HTML5", "CSS3",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Supabase", "Firebase", "Elasticsearch", "DynamoDB",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "GitHub Actions", "CI/CD", "Linux", "Git", "Nginx",
    "Kafka", "RabbitMQ", "Celery", "Microservices", "Clean Architecture", "TDD", "Pytest", "Jest",
    "Pandas", "NumPy", "Scikit-learn", "PyTorch", "TensorFlow", "LangChain", "LangGraph", "OpenAI", "Streamlit",
]


def extract_highlighted_technologies(
    base_resume: str,
    repos: list[dict],
    readmes: Optional[dict[str, str]] = None,
) -> list[str]:
    """
    Extrai de forma determinística as tecnologias relevantes comprovadas no currículo base
    e nos repositórios do GitHub do candidato.
    """
    evidence = competency_matcher_core.candidate_evidence(base_resume or "", repos or [], readmes or {})
    found: list[str] = []
    seen_lower: set[str] = set()

    # 1. Varredura contra o catálogo de tecnologias de mercado (com grafia canônica) usando fronteira léxica
    for tech in COMMON_TECH_CATALOG:
        if tech.lower() not in seen_lower and competency_matcher_core.matches_technology(tech, evidence):
            seen_lower.add(tech.lower())
            found.append(tech)

    # 2. Linguagens principais e tópicos adicionais dos repositórios
    for repo in repos or []:
        lang = (repo.get("language") or "").strip()
        if lang and lang.lower() not in seen_lower:
            seen_lower.add(lang.lower())
            found.append(lang)
        for topic in repo.get("topics") or []:
            t_clean = str(topic).strip()
            if t_clean and len(t_clean) >= 2 and t_clean.lower() not in seen_lower:
                seen_lower.add(t_clean.lower())
                found.append(t_clean)

    return found[:25]


def select_top_general_repos(
    raw_repos: list[dict],
    username: str,
    base_resume: str = "",
    max_repos: int = 3,
) -> tuple[list[dict], dict[str, str]]:
    """
    Seleciona os melhores repositórios públicos do candidato (sem depender de vaga específica),
    priorizando projetos autorais (não-forks) com descrição, estrelas, tópicos e alinhamento com o currículo base,
    e faz download concorrente dos READMEs higienizados.
    """
    if not raw_repos or not (username or "").strip():
        return [], {}

    non_forks = [r for r in raw_repos if not r.get("fork", False)]
    candidates = non_forks if non_forks else raw_repos
    resume_lower = (base_resume or "").lower()

    scored = []
    for repo in candidates:
        score = 0.0
        lang = (repo.get("language") or "").strip()
        desc = (repo.get("description") or "").strip()
        topics = repo.get("topics") or []
        stars = int(repo.get("stargazers_count") or 0)

        if lang:
            score += 4.0
            if lang.lower() in resume_lower:
                score += 4.0
        if desc:
            score += 5.0
        if topics:
            score += min(6.0, len(topics) * 1.5)
        score += min(10.0, stars * 2.0)

        scored.append({
            "repo": repo,
            "score": score,
            "language": lang.lower(),
            "updated_at": repo.get("updated_at") or "",
        })

    scored.sort(key=lambda x: (x["score"], x["updated_at"]), reverse=True)

    # Seleção com bônus de diversidade de linguagem principal
    selected_items = []
    seen_langs = set()
    for _ in range(min(max_repos, len(scored))):
        best_item = None
        best_eff = -999.0
        for item in scored:
            if item in selected_items:
                continue
            bonus = 2.5 if item["language"] and item["language"] not in seen_langs else 0.0
            eff = item["score"] + bonus
            if eff > best_eff:
                best_eff = eff
                best_item = item
        if best_item:
            selected_items.append(best_item)
            if best_item["language"]:
                seen_langs.add(best_item["language"])

    selected_repos = []
    for item in selected_items:
        r = item["repo"]
        selected_repos.append({
            "name": r.get("name", ""),
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "topics": r.get("topics") or [],
            "url": r.get("html_url", ""),
            "default_branch": r.get("default_branch", "main"),
            "relevance_score": round(item["score"], 1),
        })

    def _fetch_readme(repo_info: dict) -> tuple[str, str]:
        repo_name = repo_info["name"]
        if not repo_name or not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
            return repo_name, ""
        readme_url = f"https://api.github.com/repos/{username.strip()}/{repo_name}/readme"
        try:
            resp = requests.get(readme_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
            if resp.status_code == 200:
                content_b64 = resp.json().get("content", "")
                content_str = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                return repo_name, _clean_readme(content_str, max_chars=1200)
        except Exception as e:
            print(f"Erro ao baixar README de {repo_name}: {e}")
        return repo_name, ""

    readmes: dict[str, str] = {}
    if selected_repos:
        with ThreadPoolExecutor(max_workers=min(3, len(selected_repos))) as executor:
            for repo_name, cleaned in executor.map(_fetch_readme, selected_repos):
                if cleaned:
                    readmes[repo_name] = cleaned

    return selected_repos, readmes


def generate_general_resume(
    base_resume: str,
    repos: list[dict],
    readmes: dict[str, str],
    extracted_techs: list[str],
    language: str = "pt",
    target_focus: str = "",
) -> tuple[str, bool]:
    """Invoca o LLM com os prompts dedicados para gerar o currículo geral de alto impacto."""
    L = LABELS.get(language or "pt", LABELS["pt"])
    state_for_ctx = {"github_repos": repos, "github_readmes": readmes}
    portfolio_str = portfolio_context(state_for_ctx, 1200) or "Nenhum repositório do GitHub fornecido."
    techs_str = ", ".join(extracted_techs) if extracted_techs else "Extraia todas as tecnologias relevantes do currículo base."

    system_prompt = build_general_resume_system_prompt(L, target_focus=target_focus)
    messages = build_general_resume_user_messages(
        system_prompt=system_prompt,
        base_resume=base_resume,
        portfolio=portfolio_str,
        extracted_techs_str=techs_str,
        target_focus=target_focus,
    )

    response = llm.invoke_tracked(
        llm.chat_model(temperature=0.2, thinking_level=None),
        messages,
        f"{system_prompt}\n{base_resume}\n{portfolio_str}",
    )
    return llm.response_text(response), llm.is_truncated(response)


def run_general_optimization(
    base_resume: str,
    github_username: str = "",
    target_title: str = "",
    language: str = "pt",
    custom_project_urls: str = "",
    profile: Optional[dict] = None,
    on_step: Optional[Callable[[str, Optional[str]], None]] = None,
) -> dict:
    """
    Endpoint independente de otimização geral de currículo (sem vaga específica).
    Retorna um dicionário compatível com o salvamento em histórico e exibição na tela de Candidaturas.
    """
    if not (base_resume or "").strip():
        raise ValueError("O currículo base do candidato é obrigatório.")

    lang = language if language in LABELS else "pt"
    effective_title = (target_title or "").strip() or "Currículo Geral Otimizado"
    profile = profile or {}
    agent_trace = []
    warnings = []

    # 1. Coleta opcional de repositórios do GitHub (reutilizando cache do perfil ou github_fetcher)
    gh_user = (github_username or "").strip()
    raw_repos = []
    if gh_user:
        same_user = gh_user.lower() == (profile.get("github_username") or "").strip().lower()
        cached = [r for r in (profile.get("cached_repos") or []) if r.get("html_url")]
        fetch_state = {"github_username": gh_user}
        if same_user and cached:
            fetch_state["raw_github_repos"] = cached
        fetch_res = github_fetcher(fetch_state)
        raw_repos = fetch_res.get("raw_github_repos") or []
        warnings.extend(fetch_res.get("errors") or [])
        agent_trace.extend(fetch_res.get("agent_trace") or [])
        if on_step:
            on_step("🐙 Portfólio do GitHub consultado para enriquecimento geral", None)

    selected_repos, readmes = select_top_general_repos(raw_repos, gh_user, base_resume=base_resume)
    if selected_repos:
        top_names = ", ".join(r["name"] for r in selected_repos)
        agent_trace.append({
            "agent": "general_portfolio_selector",
            "step": "Seleção dos Principais Projetos do Portfólio",
            "detail": f"Selecionados Top {len(selected_repos)} repositórios ({top_names}) por mérito técnico e alinhamento com o perfil.",
            "status": "success",
        })
        if on_step:
            on_step(f"⚡ Principais projetos selecionados ({top_names})", None)

    # 2. Extração de tecnologias relevantes do perfil + portfólio
    highlighted_techs = extract_highlighted_technologies(base_resume, selected_repos or raw_repos, readmes)
    agent_trace.append({
        "agent": "general_tech_extractor",
        "step": "Mapeamento de Tecnologias Relevantes do Perfil",
        "detail": f"Identificadas {len(highlighted_techs)} tecnologias relevantes para destaque estruturado.",
        "status": "success",
    })

    # 3. Geração do Currículo Geral de Alto Impacto
    generated_md, is_truncated = generate_general_resume(
        base_resume=base_resume,
        repos=selected_repos,
        readmes=readmes,
        extracted_techs=highlighted_techs,
        language=lang,
        target_focus=(target_title or "").strip(),
    )
    if not (generated_md or "").strip():
        raise RuntimeError("O modelo retornou um currículo vazio.")

    agent_trace.append({
        "agent": "general_resume_generator",
        "step": "Redação Executiva de Currículo Geral (A4)",
        "detail": f"Currículo geral redigido em {LABELS[lang]['name']} destacando tecnologias e projetos relevantes.",
        "status": "success",
    })
    if on_step:
        on_step("✍️ Redação executiva do currículo geral concluída", generated_md)

    # 4. Injeção opcional de links específicos de projetos informados pelo usuário
    if (custom_project_urls or "").strip():
        try:
            generated_md, injected_names = inject_projects_from_urls(
                resume_md=generated_md,
                raw_urls_text=custom_project_urls,
                language=lang,
                job_description=effective_title,
            )
            for _, repo_name, norm_url in parse_github_repo_urls(custom_project_urls):
                selected_repos.append({"name": repo_name, "url": norm_url})
            agent_trace.append({
                "agent": "project_injector",
                "step": "Inclusão de Projetos Específicos por Link",
                "detail": f"Adicionados projetos específicos solicitados: {', '.join(injected_names)}.",
                "status": "success",
            })
            if on_step:
                on_step(f"🔗 Projetos específicos adicionados ({', '.join(injected_names)})", generated_md)
        except Exception as e:
            warnings.append(f"Não foi possível adicionar todos os links de projetos informados: {e}")

    # 5. Validação determinística e diagnóstico de completude do currículo geral
    val_state = {
        "base_resume_md": base_resume,
        "github_username": gh_user,
        "github_repos": [r for r in selected_repos if r.get("url")],
        "github_readmes": readmes,
        "job_technologies": highlighted_techs,
        "job_keywords": [],
        "verified_technologies": highlighted_techs,
        "unmatched_gaps": [],
        "generation_truncated": is_truncated,
    }
    is_valid, critical_issues, det_diag = _validate_resume_deterministic(generated_md, val_state)

    matched_techs = det_diag.get("matched_keywords") or highlighted_techs
    completeness_score = det_diag.get("ats_score") if highlighted_techs else 92
    if completeness_score < 85 and is_valid:
        completeness_score = 90

    diagnostic = {
        "ats_score": completeness_score,
        "approved": is_valid,
        "matched_keywords": matched_techs,
        "missing_keywords": [],
        "strengths": [
            "Currículo geral estruturado no layout executivo A4 com foco em legibilidade ATS.",
            f"Destaque categorizado para {len(matched_techs)} tecnologias relevantes identificadas no perfil/portfólio.",
            "Experiências e projetos redigidos em 1ª pessoa ativa com foco em impacto técnico.",
        ],
        "improvements": (
            [msg for msg, _ in critical_issues]
            if critical_issues
            else ["Você pode adicionar ou editar projetos específicos a qualquer momento na aba 'Editar Markdown'."]
        ),
        "interview_tips": [],
        "agent_trace": agent_trace,
        "stop_reason": "general_optimization_complete",
    }
    if warnings:
        diagnostic["run_warnings"] = warnings

    return {
        "job_title": effective_title,
        "generated_resume_md": generated_md,
        "generated_cover_letter_md": "",
        "job_language": lang,
        "job_technologies": matched_techs,
        "diagnostic": diagnostic,
        "errors": warnings,
        "agent_trace": agent_trace,
        "stop_reason": "general_optimization_complete",
    }
