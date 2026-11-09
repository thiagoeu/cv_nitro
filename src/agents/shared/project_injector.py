"""Coleta de repositórios avulsos por URL do GitHub e inserção incremental na seção de projetos do currículo."""
import base64
import re
from typing import List, Tuple
import requests
from src.agents.shared import llm
from src.agents.shared.github_scoring import GITHUB_TIMEOUT, _github_headers, _clean_readme
from src.agents.shared.sections import LABELS, resolve_section, split_sections, splice_markdown_section
from src.agents.prompts.writer_prompts import PROJECT_INJECTOR_PROMPT

GITHUB_REPO_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})/([a-zA-Z0-9_.-]+)",
    re.IGNORECASE,
)


def parse_github_repo_urls(raw_text: str) -> List[Tuple[str, str, str]]:
    """
    Extrai uma lista única de tuplas (owner, repo, canonical_url) a partir de um texto
    contendo um ou mais links de repositórios do GitHub.
    """
    if not raw_text or not raw_text.strip():
        return []

    found: List[Tuple[str, str, str]] = []
    seen = set()
    for match in GITHUB_REPO_URL_RE.finditer(raw_text):
        owner = match.group(1).strip()
        repo = match.group(2).strip()
        if repo.lower().endswith(".git"):
            repo = repo[:-4]
        repo = repo.rstrip("/.,;)")
        if not owner or not repo:
            continue
        key = f"{owner.lower()}/{repo.lower()}"
        if key not in seen:
            seen.add(key)
            found.append((owner, repo, f"https://github.com/{owner}/{repo}"))
    return found


def fetch_single_github_repo(owner: str, repo: str) -> dict:
    """
    Consulta os metadados e o README.md higienizado de um único repositório público no GitHub.
    Lança ValueError com mensagem amigável caso o repositório não exista ou a API falhe.
    """
    repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        resp = requests.get(repo_api_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
    except requests.exceptions.Timeout:
        raise ValueError(f"Tempo limite esgotado ao consultar o repositório '{owner}/{repo}' no GitHub.")
    except Exception as e:
        raise ValueError(f"Erro de conexão ao consultar '{owner}/{repo}' no GitHub: {e}")

    if resp.status_code == 404:
        raise ValueError(f"Repositório '{owner}/{repo}' não encontrado ou privado no GitHub (HTTP 404).")
    if resp.status_code == 403:
        raise ValueError("Limite de requisições da API do GitHub atingido (HTTP 403). Configure GITHUB_TOKEN no .env.")
    if resp.status_code != 200:
        raise ValueError(f"Falha ao obter dados do repositório '{owner}/{repo}' (HTTP {resp.status_code}).")

    data = resp.json() if isinstance(resp.json(), dict) else {}
    canonical_url = data.get("html_url") or f"https://github.com/{owner}/{repo}"

    readme_text = ""
    readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    try:
        r_resp = requests.get(readme_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
        if r_resp.status_code == 200:
            content_b64 = r_resp.json().get("content", "")
            raw_md = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            readme_text = _clean_readme(raw_md, max_chars=1200)
    except Exception:
        pass

    return {
        "name": data.get("name") or repo,
        "url": canonical_url,
        "language": data.get("language") or "Multi-stack",
        "topics": data.get("topics") or [],
        "description": data.get("description") or "",
        "readme": readme_text,
    }


def generate_project_entry_md(repo_data: dict, language: str = "pt", job_description: str = "") -> str:
    """
    Usa o LLM para redigir o bloco Markdown de um projeto no padrão exato da seção
    de projetos em destaque do currículo e no idioma da candidatura.
    """
    lang_code = (language or "pt").lower()
    L = LABELS.get(lang_code, LABELS["pt"])

    formatted_prompt = PROJECT_INJECTOR_PROMPT.format(
        language=L["name"],
        repo_name=repo_data.get("name", "Projeto"),
        repo_url=repo_data.get("url", ""),
        repo_label=L["repo"],
        repo_language=repo_data.get("language") or "Multi-stack",
        repo_topics=", ".join(repo_data.get("topics") or []) or "Não informado",
        repo_description=repo_data.get("description") or "Sem descrição curta cadastrada.",
        repo_readme=repo_data.get("readme") or "README não disponível.",
        job_context=(job_description or "Destaque a arquitetura, tecnologias e impacto técnico do projeto.")[:1000],
    )

    response = llm.invoke_tracked(
        llm.chat_model(temperature=0.2, thinking_level="low"),
        formatted_prompt,
        formatted_prompt,
    )
    entry_md = llm.response_text(response).strip()
    # Remove eventual cerca de código ou cabeçalho H2 caso o modelo tenha incluído
    entry_md = re.sub(r"^```(?:markdown|md)?\s*|\s*```$", "", entry_md, flags=re.IGNORECASE).strip()
    entry_md = re.sub(r"(?m)^##\s+[^\n]+\n+", "", entry_md).strip()
    if not entry_md.startswith("### "):
        entry_md = f"### {entry_md}"

    repo_url = (repo_data.get("url") or "").strip()
    if repo_url and repo_url.lower() not in entry_md.lower():
        entry_md += f"\n- **{L['repo']}:** {repo_url}"

    return entry_md


def append_project_to_resume_md(
    resume_md: str,
    new_project_entry_md: str,
    repo_url: str,
    language: str = "pt",
) -> str:
    """
    Insere ou atualiza incrementalmente um projeto na seção de projetos do currículo Markdown,
    preservando todos os demais projetos existentes e o layout canônico.
    """
    resume_md = (resume_md or "").strip()
    entry_clean = (new_project_entry_md or "").strip()
    if not entry_clean:
        return resume_md

    lang_code = (language or "pt").lower()
    L = LABELS.get(lang_code, LABELS["pt"])
    target_sec_title = resolve_section(resume_md, L["projects"], L)

    # Caso o currículo ainda não tenha seção de projetos, cria a seção
    if not target_sec_title:
        sec_header = L["projects"]
        if not resume_md:
            return f"## {sec_header}\n{entry_clean}"
        return f"{resume_md}\n\n## {sec_header}\n{entry_clean}"

    sections = split_sections(resume_md)
    current_body = ""
    for title, body in sections:
        if title == target_sec_title:
            current_body = (body or "").strip()
            break

    # Divide o corpo atual da seção de projetos em sub-blocos por '### '
    blocks = [b.strip() for b in re.split(r"(?m)(?=^###\s+)", current_body) if b.strip()]
    norm_url = (repo_url or "").strip().rstrip("/").lower()

    replaced = False
    updated_blocks = []
    for block in blocks:
        if norm_url and norm_url in block.lower():
            updated_blocks.append(entry_clean)
            replaced = True
        else:
            updated_blocks.append(block)

    if not replaced:
        updated_blocks.append(entry_clean)

    new_section_body = "\n\n".join(updated_blocks)
    return splice_markdown_section(resume_md, target_sec_title, f"## {target_sec_title}\n{new_section_body}")


def inject_projects_from_urls(
    resume_md: str,
    raw_urls_text: str,
    language: str = "pt",
    job_description: str = "",
) -> Tuple[str, List[str]]:
    """
    Fluxo completo: valida e extrai URLs do GitHub, baixa metadados + README de cada repositório,
    gera o bloco formatado via IA e anexa incrementalmente ao currículo.
    Retorna (updated_resume_md, added_repo_names).
    """
    parsed_repos = parse_github_repo_urls(raw_urls_text)
    if not parsed_repos:
        raise ValueError("Informe ao menos um link válido de repositório do GitHub (ex.: https://github.com/usuario/projeto).")

    updated_md = resume_md
    added_names: List[str] = []
    for owner, repo, canonical_url in parsed_repos:
        repo_data = fetch_single_github_repo(owner, repo)
        entry_md = generate_project_entry_md(repo_data, language=language, job_description=job_description)
        updated_md = append_project_to_resume_md(
            updated_md,
            entry_md,
            repo_url=repo_data.get("url") or canonical_url,
            language=language,
        )
        added_names.append(repo_data.get("name") or repo)

    return updated_md, added_names

