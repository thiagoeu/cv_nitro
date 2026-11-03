"""Agentes de portfólio: coleta de repositórios no GitHub, ranqueamento e extratos dos READMEs."""
import base64
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List
import requests
from src.core import config

GITHUB_TIMEOUT = (5.0, 10.0)


def _score_repository(repo: dict, target_technologies: List[str]) -> float:
    """
    Pontua a relevância de um repositório para a vaga alvo de forma determinística (0 tokens de LLM).
    Considera forks (penalizados/ignorados), linguagem principal, topics/tags, descrição com word boundaries e estrelas.
    """
    if repo.get("fork", False):
        return -1.0

    score = 0.0
    tech_set = {t.lower().strip() for t in target_technologies if t and t.strip()}
    if not tech_set:
        return 1.0

    # 1. Correspondência de linguagem principal (+4.0)
    repo_lang = (repo.get("language") or "").strip().lower()
    if repo_lang and repo_lang in tech_set:
        score += 4.0

    # 2. Correspondência em topics/tags (+2.5 por tópico coincidente)
    for topic in repo.get("topics", []) or []:
        topic_clean = str(topic).strip().lower()
        if topic_clean in tech_set:
            score += 2.5

    # 3. Correspondência na descrição com word boundaries para evitar falsos positivos (+1.5 por termo)
    desc = str(repo.get("description") or "").lower()
    if desc:
        for tech in tech_set:
            # Word boundary regex previne que "c" case com "react", "go" com "google", etc.
            pattern = rf"(?<!\w){re.escape(tech)}(?!\w)"
            if re.search(pattern, desc):
                score += 1.5

    # 4. Bônus por popularidade (estrelas)
    stars = int(repo.get("stargazers_count") or 0)
    if stars > 0:
        score += min(2.0, stars * 0.2)

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


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = config.GITHUB_TOKEN
    if token and "your_github_token_here" not in token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


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
    Ranqueia por relevância ponderada, seleciona os Top 3 e baixa seus READMEs limpos.
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

    # Ranqueamento determinístico por score e data de atualização
    scored_repos = []
    for repo in candidate_repos:
        score = _score_repository(repo, technologies)
        scored_repos.append((score, repo))

    scored_repos.sort(key=lambda item: (item[0], item[1].get("updated_at") or ""), reverse=True)

    selected_repos = []
    for score, repo in scored_repos[:3]:
        selected_repos.append({
            "name": repo.get("name", ""),
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "url": repo.get("html_url", ""),
            "default_branch": repo.get("default_branch", "main"),
            "relevance_score": score
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


def portfolio_context(state: dict, readme_chars: int = 1200) -> str:
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
