"""Agentes de portfólio: coleta de repositórios no GitHub e curadoria MMR com extratos de READMEs."""
import base64
import re
from concurrent.futures import ThreadPoolExecutor
import requests
from src.agents.shared.context import portfolio_context
from src.agents.shared.github_scoring import (
    GITHUB_TIMEOUT,
    _github_headers,
    _clean_readme,
    _score_repository_with_matches,
    _score_repository,
)


def github_fetcher(state: dict) -> dict:
    """
    Busca repositórios públicos brutos do usuário no GitHub de forma independente.
    Executa concorrentemente com o job_analyzer na entrada do grafo.
    Repositórios já presentes no estado (cache do perfil) são reaproveitados sem chamar a API.
    """
    if state.get("raw_github_repos"):
        cached_count = len(state["raw_github_repos"])
        return {
            "raw_github_repos": state["raw_github_repos"],
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": f"Reaproveitados {cached_count} repositórios do cache do perfil sem chamadas à API.",
                "status": "info"
            }]
        }

    username = (state.get("github_username") or "").strip()
    if not username:
        return {
            "raw_github_repos": [],
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": "Nenhum usuário do GitHub informado. Etapa de portfólio ignorada.",
                "status": "info"
            }]
        }

    # Validação de segurança do nome de usuário do GitHub
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
        msg = f"Nome de usuário GitHub inválido ou potencialmente inseguro: '{username}'."
        print(msg)
        return {
            "raw_github_repos": [],
            "errors": [msg],
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": msg,
                "status": "error"
            }]
        }

    repos_url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=100"

    try:
        response = requests.get(repos_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
        if response.status_code == 403:
            msg = "Limite de requisições da API do GitHub atingido (HTTP 403). Configure GITHUB_TOKEN no .env."
            print(msg)
            return {
                "raw_github_repos": [],
                "errors": [msg],
                "agent_trace": [{
                    "agent": "github_fetcher",
                    "step": "Coleta de Repositórios GitHub",
                    "detail": msg,
                    "status": "warning"
                }]
            }
        elif response.status_code == 404:
            msg = f"Usuário '{username}' não foi encontrado no GitHub (HTTP 404)."
            print(msg)
            return {
                "raw_github_repos": [],
                "errors": [msg],
                "agent_trace": [{
                    "agent": "github_fetcher",
                    "step": "Coleta de Repositórios GitHub",
                    "detail": msg,
                    "status": "warning"
                }]
            }
        elif response.status_code != 200:
            msg = f"Falha ao acessar GitHub para '{username}' (HTTP {response.status_code})."
            print(msg)
            return {
                "raw_github_repos": [],
                "errors": [msg],
                "agent_trace": [{
                    "agent": "github_fetcher",
                    "step": "Coleta de Repositórios GitHub",
                    "detail": msg,
                    "status": "warning"
                }]
            }

        repos = response.json()
        if not isinstance(repos, list):
            return {
                "raw_github_repos": [],
                "agent_trace": [{
                    "agent": "github_fetcher",
                    "step": "Coleta de Repositórios GitHub",
                    "detail": "Resposta inesperada da API do GitHub (não retornou lista).",
                    "status": "warning"
                }]
            }
        return {
            "raw_github_repos": repos,
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": f"Consultados {len(repos)} repositórios públicos de '{username}'.",
                "status": "success"
            }]
        }
    except requests.exceptions.Timeout:
        msg = "Tempo limite esgotado ao conectar à API do GitHub."
        print(msg)
        return {
            "raw_github_repos": [],
            "errors": [msg],
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": msg,
                "status": "warning"
            }]
        }
    except Exception as e:
        msg = f"Erro no GitHub Fetcher: {e}"
        print(msg)
        return {
            "raw_github_repos": [],
            "errors": [msg],
            "agent_trace": [{
                "agent": "github_fetcher",
                "step": "Coleta de Repositórios GitHub",
                "detail": msg,
                "status": "error"
            }]
        }


def relevance_ranker(state: dict) -> dict:
    """
    Nó determinístico de sincronização (0 tokens de LLM):
    Recebe os repositórios do github_fetcher e as tecnologias da vaga do job_analyzer.
    Ranqueia por relevância ponderada com MMR, seleciona os Top 3 e baixa seus READMEs limpos.
    """
    raw_repos = state.get("raw_github_repos") or []
    username = (state.get("github_username") or "").strip()
    technologies = state.get("job_technologies", []) or []

    if not raw_repos or not username:
        return {
            "github_repos": [],
            "github_readmes": {},
            "agent_trace": [{
                "agent": "relevance_ranker",
                "step": "Curadoria e Ranqueamento de Repositórios",
                "detail": "Nenhum repositório disponível para ranqueamento.",
                "status": "info"
            }]
        }

    # Prioriza repositórios autorais (não-forks); se todos forem forks, mantém como fallback
    non_forks = [r for r in raw_repos if not r.get("fork", False)]
    candidate_repos = non_forks if non_forks else raw_repos

    job_title = state.get("job_title", "")

    # Avaliação de score base e tecnologias cobertas por cada repositório
    repo_evaluations = []
    for repo in candidate_repos:
        score, matched = _score_repository_with_matches(repo, technologies, job_title)
        repo_evaluations.append({
            "repo": repo,
            "base_score": score,
            "matched_techs": matched,
            "updated_at": repo.get("updated_at") or "",
        })

    # Seleção gulosa diversificada (MMR - Maximal Marginal Relevance)
    selected_evals = []
    covered_techs = set()
    title_techs = {t for t in technologies if t.lower() in job_title.lower()}

    for _ in range(min(3, len(repo_evaluations))):
        best_candidate = None
        best_effective_score = -999.0
        for item in repo_evaluations:
            if item in selected_evals:
                continue
            new_techs = item["matched_techs"] - covered_techs
            new_title_techs = new_techs & title_techs
            diversity_bonus = (len(new_techs) * 3.0) + (len(new_title_techs) * 8.0)
            effective_score = item["base_score"] + diversity_bonus
            if effective_score > best_effective_score:
                best_effective_score = effective_score
                best_candidate = item
            elif effective_score == best_effective_score and best_candidate:
                if item["updated_at"] > best_candidate["updated_at"]:
                    best_candidate = item

        if best_candidate and best_candidate["base_score"] >= 0:
            selected_evals.append(best_candidate)
            covered_techs |= best_candidate["matched_techs"]

    # Fallback se a seleção diversa não preencheu 3 repositórios
    if len(selected_evals) < 3 and len(repo_evaluations) > len(selected_evals):
        repo_evaluations.sort(key=lambda x: (x["base_score"], x["updated_at"]), reverse=True)
        for item in repo_evaluations:
            if item not in selected_evals:
                selected_evals.append(item)
                if len(selected_evals) == 3:
                    break

    selected_repos = []
    for item in selected_evals:
        repo = item["repo"]
        selected_repos.append({
            "name": repo.get("name", ""),
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "url": repo.get("html_url", ""),
            "default_branch": repo.get("default_branch", "main"),
            "relevance_score": item["base_score"]
        })

    def fetch_readme(repo_info: dict) -> tuple[str, str]:
        repo_name = repo_info["name"]
        if not repo_name or not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
            return repo_name, ""
        readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        try:
            readme_resp = requests.get(readme_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
            if readme_resp.status_code == 200:
                content_b64 = readme_resp.json().get("content", "")
                content_str = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                return repo_name, _clean_readme(content_str, max_chars=1200)
        except Exception as e:
            print(f"Erro ao baixar README de {repo_name}: {e}")
        return repo_name, ""

    readmes = {}
    if selected_repos:
        with ThreadPoolExecutor(max_workers=min(3, len(selected_repos))) as executor:
            results = executor.map(fetch_readme, selected_repos)
            for repo_name, cleaned_readme in results:
                if cleaned_readme:
                    readmes[repo_name] = cleaned_readme

    top_names = ", ".join(r["name"] for r in selected_repos)
    return {
        "github_repos": selected_repos,
        "github_readmes": readmes,
        "agent_trace": [{
            "agent": "relevance_ranker",
            "step": "Curadoria Concorrente de Portfólio",
            "detail": f"Selecionados Top {len(selected_repos)} repositórios ({top_names}) com READMEs obtidos concorrentemente.",
            "status": "success"
        }]
    }
