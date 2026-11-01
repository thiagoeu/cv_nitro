import re
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from src.core import config
import requests
import base64
from langchain_core.messages import HumanMessage, SystemMessage

MAX_REVIEW_ATTEMPTS = 2
LLM_TIMEOUT_SECONDS = 120
GITHUB_TIMEOUT = (5.0, 10.0)

# Rótulos canônicos por idioma: o template do prompt usa estes valores para não vazar português em vagas EN/ES.
LABELS = {
    "pt": {
        "name": "PORTUGUÊS (Brasil)", "summary": "RESUMO PROFISSIONAL", "skills": "HABILIDADES TÉCNICAS",
        "experience": "EXPERIÊNCIA PROFISSIONAL", "projects": "PROJETOS EM DESTAQUE", "education": "FORMAÇÃO ACADÊMICA",
        "certifications": "CURSOS E CERTIFICAÇÕES", "languages": "IDIOMAS",
        "table_header": "| Categoria | Tecnologias & Conceitos |",
        "categories": "Back-end & Arquitetura, Front-end & Mobile, Banco de Dados & ORM, DevOps & Ferramentas",
        "repo": "Repositório",
    },
    "en": {
        "name": "INGLÊS (English)", "summary": "PROFESSIONAL SUMMARY", "skills": "TECHNICAL SKILLS",
        "experience": "WORK EXPERIENCE", "projects": "KEY PROJECTS", "education": "EDUCATION",
        "certifications": "CERTIFICATIONS", "languages": "LANGUAGES",
        "table_header": "| Category | Technologies & Concepts |",
        "categories": "Back-end & Architecture, Front-end & Mobile, Databases & ORM, DevOps & Tools",
        "repo": "Repository",
    },
    "es": {
        "name": "ESPANHOL (Español)", "summary": "RESUMEN PROFESIONAL", "skills": "HABILIDADES TÉCNICAS",
        "experience": "EXPERIENCIA PROFESIONAL", "projects": "PROYECTOS DESTACADOS", "education": "FORMACIÓN ACADÉMICA",
        "certifications": "CURSOS Y CERTIFICACIONES", "languages": "IDIOMAS",
        "table_header": "| Categoría | Tecnologías y Conceptos |",
        "categories": "Back-end y Arquitectura, Front-end y Mobile, Bases de Datos y ORM, DevOps y Herramientas",
        "repo": "Repositorio",
    },
}

def _llm(temperature: float, thinking_level: Optional[str] = "low") -> ChatGoogleGenerativeAI:
    """Cliente Gemini único: timeout/retries limitados evitam travar a UI; thinking 'low' corta a latência nas tarefas curtas."""
    extra = {"thinking_level": thinking_level} if thinking_level else {}
    # 120s por tentativa e 1 retry por modelo: a cadeia de fallbacks cuida do resto (pior caso ~12 min, não ~45)
    def make(model: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, timeout=LLM_TIMEOUT_SECONDS, max_retries=1, **extra)
    fallbacks = []
    if config.GEMINI_FALLBACK_MODEL and config.GEMINI_FALLBACK_MODEL != config.GEMINI_MODEL:
        fallbacks.append(make(config.GEMINI_FALLBACK_MODEL))
    if config.GROQ_API_KEY:
        # Tokens de raciocínio contam no limite por minuto do Groq; só o gpt-oss aceita "low".
        groq_extra = {"reasoning_effort": thinking_level} if thinking_level and config.GROQ_MODEL.startswith("openai/gpt-oss") else {}
        fallbacks.append(ChatGroq(model=config.GROQ_MODEL, temperature=temperature, timeout=LLM_TIMEOUT_SECONDS, max_retries=1, **groq_extra))
    if not fallbacks:
        return make(config.GEMINI_MODEL)
    # Cadeia plana (with_fallbacks aninhado perde os reservas no with_structured_output).
    # Qualquer erro troca de modelo: a cota 429 do free tier do Gemini é por modelo e estoura rápido.
    return make(config.GEMINI_MODEL).with_fallbacks(fallbacks)

def _text(response) -> str:
    """Extrai o texto puro de respostas de LLM (Gemini, Groq, AIMessage). Remove cercas ```markdown."""
    if hasattr(response, "text") and isinstance(response.text, str):
        text = response.text
    elif hasattr(response, "content"):
        if isinstance(response.content, str):
            text = response.content
        elif isinstance(response.content, list):
            parts = []
            for item in response.content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            text = "".join(parts)
        else:
            text = str(response.content)
    else:
        text = str(response)
    return re.sub(r"^```(?:markdown|md)?\s*\n(.*?)\n?```$", r"\1", text.strip(), flags=re.DOTALL).strip()

class JobAnalysis(BaseModel):
    keywords: List[str] = Field(description="Principais palavras-chave, soft-skills e conceitos importantes da vaga.")
    technologies: List[str] = Field(description="Ferramentas, linguagens e frameworks técnicos exigidos ou desejados.")
    language: Literal["pt", "en", "es"] = Field(description="Idioma em que a vaga está escrita: 'en' inglês, 'pt' português, 'es' espanhol.")
    summary: str = Field(description=(
        "Resumo enxuto da vaga escrito no MESMO idioma da vaga (vaga em inglês → resumo em inglês), em tópicos curtos (máx. ~150 palavras): empresa e produto em uma frase, "
        "cargo e senioridade, responsabilidades, requisitos obrigatórios e desejáveis. Exclua texto institucional genérico, "
        "benefícios, declarações de diversidade e textos da interface do site."
    ))

def job_analyzer(state: dict) -> dict:
    """
    Analisa a descrição da vaga e extrai palavras-chave, tecnologias e o idioma predominante.
    Falhas do modelo são propagadas: sem idioma/tecnologias o restante do fluxo geraria um resultado errado.
    """
    job_description = state.get("job_description", "")

    if not job_description:
        return {"job_keywords": [], "job_technologies": [], "job_language": "pt", "job_summary": ""}

    structured_llm = _llm(temperature=0).with_structured_output(JobAnalysis)
    prompt = PromptTemplate.from_template(
        "Você é um recrutador especialista. Analise a seguinte vaga de emprego "
        "e extraia as principais tecnologias, palavras-chave comportamentais/conceituais "
        "e identifique o idioma em que a vaga está escrita. Ignore textos de interface do site "
        "de vagas (ex.: 'Sobre a vaga', 'Candidatar-se') ao decidir o idioma. "
        "Escreva também um resumo enxuto da vaga, que substituirá o texto original nas próximas etapas.\n\n"
        "Vaga:\n{job_description}"
    )
    result = (prompt | structured_llm).invoke({"job_description": job_description})

    return {
        "job_keywords": result.keywords,
        "job_technologies": result.technologies,
        "job_language": result.language,
        "job_summary": result.summary
    }

def _job_context(state: dict) -> str:
    """Resumo da vaga + termos ATS no lugar do texto colado: corta boilerplate (benefícios, institucional) de cada chamada seguinte."""
    summary = state.get("job_summary")
    if not summary:
        return state.get("job_description", "")
    terms = ", ".join(dict.fromkeys((state.get("job_technologies") or []) + (state.get("job_keywords") or [])))
    return f"{summary}\n\nPalavras-chave ATS: {terms}"

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
        return {"raw_github_repos": state["raw_github_repos"]}

    username = (state.get("github_username") or "").strip()
    if not username:
        return {"raw_github_repos": []}

    # Validação de segurança do nome de usuário do GitHub
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
        msg = f"Nome de usuário GitHub inválido ou potencialmente inseguro: '{username}'."
        print(msg)
        return {"raw_github_repos": [], "errors": [msg]}

    repos_url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=100"

    try:
        response = requests.get(repos_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
        if response.status_code == 403:
            msg = "Limite de requisições da API do GitHub atingido (HTTP 403). Configure GITHUB_TOKEN no .env."
            print(msg)
            return {"raw_github_repos": [], "errors": [msg]}
        elif response.status_code == 404:
            msg = f"Usuário '{username}' não foi encontrado no GitHub (HTTP 404)."
            print(msg)
            return {"raw_github_repos": [], "errors": [msg]}
        elif response.status_code != 200:
            msg = f"Falha ao acessar GitHub para '{username}' (HTTP {response.status_code})."
            print(msg)
            return {"raw_github_repos": [], "errors": [msg]}

        repos = response.json()
        if not isinstance(repos, list):
            return {"raw_github_repos": []}
        return {"raw_github_repos": repos}
    except requests.exceptions.Timeout:
        msg = "Tempo limite esgotado ao conectar à API do GitHub."
        print(msg)
        return {"raw_github_repos": [], "errors": [msg]}
    except Exception as e:
        msg = f"Erro no GitHub Fetcher: {e}"
        print(msg)
        return {"raw_github_repos": [], "errors": [msg]}

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
        return {"github_repos": [], "github_readmes": {}}

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

    readmes = {}
    for repo in selected_repos:
        repo_name = repo["name"]
        if not repo_name or not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
            continue
        readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        try:
            readme_resp = requests.get(readme_url, headers=_github_headers(), timeout=GITHUB_TIMEOUT)
            if readme_resp.status_code == 200:
                content_b64 = readme_resp.json().get("content", "")
                content_str = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                readmes[repo_name] = _clean_readme(content_str, max_chars=1200)
        except Exception as e:
            print(f"Erro ao baixar README de {repo_name}: {e}")

    return {
        "github_repos": selected_repos,
        "github_readmes": readmes
    }

def _portfolio_context(state: dict, readme_chars: int = 1200) -> str:
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

def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown com formatação de alta fidelidade e aderência ATS,
    no idioma da vaga (traduzindo o currículo base), com tabela de habilidades e bullets de impacto.
    Uma única chamada: os extratos higienizados dos READMEs (top 3) vão direto no prompt.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = _job_context(state)
    feedback = state.get("reviewer_feedback", "")
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])

    # 1. Prefixo estático imutável: Regras ATS e Layouts (máximo reuso de Prompt Caching)
    system_prompt = f"""Você é um especialista em recrutamento executivo de tecnologia e sistemas ATS.
Sua missão é reescrever o currículo base em Markdown de ALTA FIDELIDADE e PADRONIZAÇÃO EXECUTIVA, escrito inteiramente em {L['name']}.

ESTRUTURA OBRIGATÓRIA (substitua cada <marcador> pelo conteúdo real; nunca escreva os sinais < >, colchetes ou o nome do marcador):

# <Nome completo do candidato>
### <Cargo alvo alinhado à vaga>
<Cidade, UF / País> | <Email> | <LinkedIn> | <GitHub>

## {L['summary']}
<Um único parágrafo denso destacando senioridade, stack principal alinhada à vaga, escala dos projetos e diferenciais técnicos reais>

## {L['skills']}
{L['table_header']}
| :--- | :--- |
| **<Categoria>** | <tecnologias e conceitos separados por vírgula> |

(Uma linha por categoria, ex.: {L['categories']}. Adapte as categorias ao candidato, sempre com 2 colunas e a linha separadora.)

## {L['experience']}
### <Empresa / Órgão — Projeto>
*<Cargo> | <Período> | <Localidade (Remoto ou Presencial)>*
- **<Tópico de impacto>:** <verbo de ação em 1ª pessoa + escopo + resultado mensurável ou de escala>

(3 a 5 bullets por experiência, cobrindo impacto, back-end/arquitetura, front-end, dados/integrações e processos, quando aplicável. Use SEMPRE verbos em 1ª pessoa indicando autoria própria: no cargo atual use o presente como 'Atuo...', 'Construo...', 'Desenvolvo...', 'Lidero...'; em cargos passados use o pretérito como 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Otimizei...'. NUNCA use a 3ª pessoa como 'Atua', 'Constrói', 'Desenvolveu', 'Implementou'.)

## {L['projects']}
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação em 1ª pessoa, ex: 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Projetei...'>
- **{L['repo']}:** <URL do repositório no GitHub>

(Enriqueça com os repositórios do GitHub fornecidos.)

## {L['education']}
### <Grau e curso>
*<Instituição> | <Ano de conclusão / previsão>*

## {L['certifications']}
- **<Curso / certificação>:** <Instituição> (<Ano>)

## {L['languages']}
<Idioma>: <Nível> | <Idioma>: <Nível>

REGRAS CRÍTICAS:
1. IDIOMA: todo o currículo DEVE estar em {L['name']}. Se o currículo base estiver em outro idioma, TRADUZA integralmente: resumo, cargos, bullets, tópicos, cabeçalho e categorias da tabela, formação, certificações, nomes dos idiomas e níveis. Mantenha como no original apenas nomes de pessoas, empresas, instituições, projetos e tecnologias.
2. BULLETS: sempre `- **Tópico:** ação`. Não use "●", "•" nem colchetes.
3. TABELA: a seção de habilidades é SEMPRE a tabela Markdown de 2 colunas acima, com a linha separadora `| :--- | :--- |`.
4. ATS: integre naturalmente as palavras-chave da vaga nas experiências e habilidades.
5. NUNCA ALUCINE: não invente empregos, empresas, tecnologias ou repositórios que não estejam no currículo base ou no portfólio.
6. VOZ NARRATIVA E AUTORIA EM 1ª PESSOA: Todos os bullets de experiência e projetos DEVEM ser redigidos em PRIMEIRA PESSOA ('eu fiz'), transmitindo protagonismo, proatividade e sentimento de dono (ownership).
   - Cargo/experiência atual (presente): conjugue na 1ª pessoa do presente (ex.: "Atuo no desenvolvimento...", "Construo e mantenho APIs...", "Desenvolvo testes...", "Lidero...").
   - Cargos passados e projetos (passado): conjugue na 1ª pessoa do pretérito perfeito (ex.: "Desenvolvi...", "Implementei...", "Estruturei...", "Configurei...", "Solucionei...").
   - NUNCA use verbos na 3ª pessoa (ex.: "Atua", "Constrói", "Desenvolveu", "Implementou"), pois soa impessoal e retira a autoria do candidato.
7. Retorne APENAS o Markdown do currículo, sem comentários e sem cercas de código (```)."""

    feedback_text = f"\n\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. Ajuste o currículo rigorosamente conforme esse feedback." if feedback else ""
    portfolio = _portfolio_context(state, 1200) or "Nenhum repositório do GitHub fornecido."

    # Prefixo estável primeiro (regras -> currículo base) para aproveitar o cache implícito de prompt
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}"),
        HumanMessage(content=f"--- VAGA ALVO ---\n{job_desc}\n\n--- PORTFÓLIO GITHUB ---\n{portfolio}{feedback_text}")
    ]
    response = _llm(temperature=0.2, thinking_level=None).invoke(messages)
    return {"generated_resume_md": _text(response)}

def _term_in_text(term: str, text_lower: str) -> bool:
    """Verifica presença de termo técnico respeitando limites de palavras sem falso positivo."""
    term_clean = term.lower().strip()
    if not term_clean:
        return False
    # Para termos com caracteres especiais (+, #, ., -), ex: c++, c#, .net, node.js
    pattern = rf"(?<![a-zA-Z0-9]){re.escape(term_clean)}(?![a-zA-Z0-9])"
    return bool(re.search(pattern, text_lower))

PLACEHOLDER_RE = re.compile(r"<[A-Za-zÀ-ÿ0-9\s/—–_.,:-]+>")
EMAIL_IN_BRACKETS_RE = re.compile(r"^<[^@\s]+@[^@\s]+\.[^@\s]+>$")

def _unfilled_placeholders(markdown: str):
    """Marcadores <...> não substituídos; e-mails no formato <usuario@dominio> não contam."""
    return [m for m in PLACEHOLDER_RE.finditer(markdown) if not EMAIL_IN_BRACKETS_RE.match(m.group())]

def _critical_patch_section(generated_md: str, critical_issues: list, labels: dict) -> Optional[str]:
    """
    Seção a refinar para um problema crítico determinístico, no idioma da vaga.
    URL de repositório fora do portfólio -> seção de projetos; marcador -> último '## ' antes dele.
    None quando não identificável (ex.: marcador no cabeçalho, antes da primeira seção).
    """
    if any("repositório citado" in issue for issue in critical_issues):
        return labels["projects"]
    unfilled = _unfilled_placeholders(generated_md)
    if unfilled:
        headers = re.findall(r"(?m)^##\s+(.+?)\s*$", generated_md[:unfilled[0].start()])
        return headers[-1] if headers else None
    return None

def _validate_resume_deterministic(generated_md: str, state: dict) -> tuple[bool, list[str], dict]:
    """
    Auditoria determinística Tier 1 (0 tokens de LLM):
    1. Placeholders residuais (<Nome>, <Empresa>, etc.) - Crítico
    2. Integridade de URLs de repositórios citados vs repositórios obtidos do GitHub - Crítico
    3. Conformidade da tabela de habilidades (aviso e cálculo estrutural)
    4. Mapeamento real de termos da vaga e cálculo auditável de ATS (0 a 100, linear)
    """
    critical_issues = []
    warnings = []
    generated_md = generated_md or ""

    # 1. Placeholders residuais: detecta padrões como <Nome>, <Cargo alvo...>, <Cidade, UF>
    # Excetua endereços de e-mail no formato <usuario@dominio.com>
    unfilled = [m.group() for m in _unfilled_placeholders(generated_md)]
    if unfilled:
        sample = ", ".join(unfilled[:3])
        critical_issues.append(f"O currículo contém marcadores de preenchimento não substituídos: {sample}")

    # 2. Integridade de URLs de repositórios do GitHub
    valid_repo_urls = set()
    for r in state.get("github_repos", []) or []:
        url = (r.get("url") or "").strip().rstrip("/").lower()
        if url:
            valid_repo_urls.add(url)
            
    username = (state.get("github_username") or "").strip().lower()
    user_profile_url = f"https://github.com/{username}".rstrip("/").lower() if username else ""

    cited_github_urls = re.findall(r"https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+", generated_md)
    for raw_url in cited_github_urls:
        url_clean = raw_url.strip().rstrip("/").lower()
        if url_clean == user_profile_url:
            continue
        if valid_repo_urls and url_clean not in valid_repo_urls:
            critical_issues.append(f"O repositório citado '{raw_url}' não consta no portfólio retornado pela API do GitHub")

    # 3. Tabela Markdown de habilidades com 2 colunas
    has_table = bool(re.search(r"\|\s*:?---+\s*\|\s*:?---+\s*\|", generated_md))
    if not has_table:
        warnings.append("A seção de habilidades deve conter uma tabela Markdown de 2 colunas com o separador '| :--- | :--- |'")

    # 4. Mapeamento de termos ATS e pontuação auditável
    job_technologies = [t.strip() for t in (state.get("job_technologies") or []) if t and t.strip()]
    job_keywords = [k.strip() for k in (state.get("job_keywords") or []) if k and k.strip()]
    gen_lower = generated_md.lower()

    matched_techs = [t for t in job_technologies if _term_in_text(t, gen_lower)]
    matched_kws = [k for k in job_keywords if _term_in_text(k, gen_lower)]

    seen = set()
    unique_matched = []
    for m in (matched_techs + matched_kws):
        if m.lower() not in seen:
            seen.add(m.lower())
            unique_matched.append(m)

    tech_rate = len(matched_techs) / max(len(job_technologies), 1)
    keyword_rate = len(matched_kws) / max(len(job_keywords), 1)
    structural_penalties = (len(critical_issues) * 0.25) + (0.20 if not has_table else 0.0)
    structural_rate = max(0.4, 1.0 - structural_penalties)

    base_score = (0.50 * tech_rate) + (0.25 * keyword_rate) + (0.25 * structural_rate)
    ats_score = int(min(100, max(0, round(base_score * 100))))

    applied_changes = [
        f"Alinhamento comprovado de {len(matched_techs)} tecnologias da vaga no histórico",
        f"Integração natural de {len(matched_kws)} palavras-chave conceituais/ATS",
        "Formatação de habilidades técnicas em tabela padronizada de 2 colunas" if has_table else "Estrutura executiva em tópicos aplicada",
        "Experiências reescritas com foco em impacto e verbos de ação"
    ]

    is_valid = len(critical_issues) == 0
    diagnostic_data = {
        "ats_score": ats_score,
        "matched_keywords": unique_matched,
        "applied_changes": applied_changes,
        "tech_coverage": round(tech_rate * 100),
        "keyword_coverage": round(keyword_rate * 100),
        "warnings": warnings
    }

    return is_valid, critical_issues, diagnostic_data

class ReviewResult(BaseModel):
    approved: bool = Field(description="True se o currículo não tiver alucinações, estiver todo no idioma pedido e seguir o padrão estrutural; False caso contrário.")
    feedback: str = Field(description="Feedback detalhado explicando o que foi corrigido ou aprovado.")
    ats_score: int = Field(default=85, description="Nota de compatibilidade ATS de 0 a 100.")
    applied_changes: List[str] = Field(default_factory=list, description="Lista com 3 a 5 melhorias ou adequações realizadas.")
    severity: Literal["approved", "minor", "major"] = Field(
        default="approved",
        description="Severidade da falha: 'approved' se aprovado; 'minor' se for correção pontual de formatação/tabela/link de uma seção específica; 'major' se houver alucinações graves de cargos ou divergência estrutural total."
    )
    target_section: Optional[str] = Field(
        default=None,
        description="Nome da seção específica a ser corrigida se severity for 'minor' (ex: 'HABILIDADES TÉCNICAS', 'PROJETOS EM DESTAQUE', 'RESUMO PROFISSIONAL', 'TECHNICAL SKILLS', 'KEY PROJECTS')."
    )

def splice_markdown_section(full_markdown: str, target_section_title: str, new_section_content: str) -> str:
    """
    Substitui cirurgicamente o bloco de uma seção Markdown específica pelo novo conteúdo fornecido.
    Localiza a seção pelo cabeçalho (## Título) de forma case-insensitive e tolerante a espaços.
    Garante integridade estrutural e fallback seguro caso a seção não seja encontrada.
    """
    if not full_markdown or not target_section_title:
        return full_markdown
    
    clean_title = re.sub(r"^[#\s]+|[#:\s]+$", "", target_section_title).strip()
    if not clean_title:
        return full_markdown

    # Normaliza new_section_content para conter o cabeçalho se omitido
    formatted_new = new_section_content.strip()
    if not re.match(r"^##\s+", formatted_new):
        formatted_new = f"## {clean_title}\n{formatted_new}"
    if not formatted_new.endswith("\n"):
        formatted_new += "\n\n"
    else:
        formatted_new += "\n"

    # Regex para encontrar a seção alvo: inicia no cabeçalho e vai até o próximo ## ou fim do texto
    pattern = rf"(?im)(^##\s*{re.escape(clean_title)}[^\n]*\n)(?:[\s\S]*?)(?=(?:^##\s+|\Z))"
    match = re.search(pattern, full_markdown)
    if match:
        return full_markdown[:match.start()] + formatted_new + full_markdown[match.end():].lstrip()

    # Fallback de busca aproximada por substring de cabeçalho
    approx_pattern = rf"(?im)(^##\s*[^\n]*{re.escape(clean_title)}[^\n]*\n)(?:[\s\S]*?)(?=(?:^##\s+|\Z))"
    approx_match = re.search(approx_pattern, full_markdown)
    if approx_match:
        return full_markdown[:approx_match.start()] + formatted_new + full_markdown[approx_match.end():].lstrip()

    return full_markdown

def section_patcher(state: dict) -> dict:
    """
    Refinamento cirúrgico de seção (Delta Section Patching):
    Reescreve exclusivamente a seção rejeitada pelo quality_reviewer (falha 'minor'),
    economizando mais de 80% dos tokens de saída em relação a uma regeneração completa.
    """
    current_resume = state.get("generated_resume_md", "") or ""
    target_section = state.get("patch_section")
    instruction = state.get("patch_instruction") or state.get("reviewer_feedback") or "Ajuste a seção conforme as diretrizes."
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])

    if not target_section or not current_resume:
        return {"generated_resume_md": current_resume}

    prompt = PromptTemplate.from_template(
        "Você é um especialista em recrutamento técnico.\n"
        "Sua tarefa é reescrever EXCLUSIVAMENTE a seção '{target_section}' do currículo abaixo em Markdown.\n\n"
        "DIRETRIZ DE REVISÃO / AJUSTE:\n"
        "{instruction}\n\n"
        "CURRÍCULO ATUAL:\n"
        "{current_resume}\n\n"
        "REGRAS:\n"
        "1. Escreva inteiramente em {language}.\n"
        "2. Se for seção de experiência ou projetos, use OBRIGATORIAMENTE verbos em 1ª PESSOA indicando autoria ('Atuo...', 'Desenvolvi...', 'Implementei...'), nunca na 3ª pessoa ('Atua', 'Desenvolveu').\n"
        "3. Retorne APENAS o bloco Markdown correspondente a esta seção, começando com '## {target_section}'.\n"
        "4. Não inclua comentários nem cercas de código (```)."
    )

    try:
        response = _llm(temperature=0.2, thinking_level="low").invoke(
            prompt.format(
                target_section=target_section,
                instruction=instruction,
                current_resume=current_resume,
                language=L["name"]
            )
        )
        patched_section_md = _text(response)
        updated_resume = splice_markdown_section(current_resume, target_section, patched_section_md)
        return {"generated_resume_md": updated_resume}
    except Exception as e:
        print(f"Erro no section_patcher: {e}")
        return {"generated_resume_md": current_resume, "errors": [f"Falha no patch cirúrgico: {e}"]}

def quality_reviewer(state: dict) -> dict:
    """
    Revisa o currículo gerado combinando validação determinística Tier 1 (0 tokens)
    com auditoria semântica Tier 2 via LLM para máxima qualidade e eficiência de tokens.
    Classifica falhas em 'minor' (para section_patcher) ou 'major' (para regeneração completa).
    """
    attempts = state.get("review_attempts", 0)
    generated_md = state.get("generated_resume_md", "") or ""
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])
    strict = state.get("strict_review", True)

    # Validação determinística preliminar (Tier 1 - zero tokens)
    is_valid, critical_issues, diag = _validate_resume_deterministic(generated_md, state)

    def verdict(approved: bool, feedback: str, severity: str, section: Optional[str] = None) -> dict:
        return {
            "reviewer_approved": approved,
            "reviewer_feedback": feedback,
            "review_attempts": attempts + 1,
            "review_severity": severity,
            "patch_section": section,
            "patch_instruction": None if approved else feedback,
            "diagnostic": {
                "ats_score": diag["ats_score"],
                "matched_keywords": diag["matched_keywords"],
                "applied_changes": diag["applied_changes"],
                "reviewer_summary": feedback
            }
        }

    if not is_valid:
        feedback_det = "Ajustes necessários no currículo: " + "; ".join(critical_issues) + "."
        target_sec = _critical_patch_section(generated_md, critical_issues, L)
        if strict:
            return verdict(False, feedback_det, "minor" if target_sec else "major", target_sec)
        # Modo econômico: um único refinamento da seção afetada, sem revisor LLM nem reescrita completa
        if target_sec and attempts == 0:
            return verdict(False, feedback_det, "minor", target_sec)
        return verdict(True, f"Aprovado em modo econômico com avisos: {'; '.join(critical_issues)}.", "approved")

    # Modo econômico (strict_review=False): utiliza apenas o diagnóstico determinístico
    if not strict:
        return verdict(True, "Aprovado em modo econômico com validação estrutural determinística.", "approved")

    # Tier 2: Auditoria semântica fina com LLM apenas se passou no Tier 1
    try:
        structured_llm = _llm(temperature=0).with_structured_output(ReviewResult)
        prompt = PromptTemplate.from_template(
            "Você é um auditor rigoroso de currículos técnicos de alto padrão e compatibilidade ATS.\n"
            "Avalie o currículo gerado segundo os critérios:\n"
            "1. **Alucinações:** o currículo cita empregos, tecnologias ou ferramentas que NÃO constam no currículo base nem nos READMEs?\n"
            "2. **Idioma:** o currículo está INTEIRAMENTE em {language} (títulos, tabela, bullets, cargos, formação, idiomas)?\n"
            "3. **Layout:** a seção de habilidades é uma tabela Markdown de 2 colunas com linha separadora, "
            "e os bullets seguem o formato `- **Tópico:** ação` (sem colchetes)?\n"
            "4. **Voz Narrativa em 1ª Pessoa:** os bullets de experiência e projetos usam verbos em 1ª pessoa ('Atuo...', 'Desenvolvi...', 'Implementei...') indicando protagonismo e autoria, e NÃO em 3ª pessoa impessoal ('Atua', 'Desenvolveu')?\n\n"
            "Avalie a qualidade ATS:\n"
            "- Atribua um ats_score de 0 a 100 baseado na fidelidade, clareza e densidade das keywords.\n"
            "- Liste em applied_changes de 3 a 5 adequações realizadas em relação ao currículo base.\n"
            "- Classifique severity em 'approved' (aprovado), 'minor' (problema pontual em 1 seção específica) ou 'major' (alucinação grave/reescrita total).\n"
            "- Se severity for 'minor', indique em target_section exatamente qual seção deve ser corrigida (ex.: 'HABILIDADES TÉCNICAS', 'PROJETOS EM DESTAQUE', 'RESUMO PROFISSIONAL').\n\n"
            "--- CURRÍCULO BASE ---\n{base_resume}\n\n"
            "--- READMEs FORNECIDOS ---\n{portfolio_context}\n\n"
            "--- CURRÍCULO GERADO (Para revisão) ---\n{generated}\n\n"
            "Retorne a análise estruturada."
        )
        result = (prompt | structured_llm).invoke({
            "language": L["name"],
            "base_resume": state.get("base_resume_md", ""),
            "portfolio_context": _portfolio_context(state, 600),
            "generated": state.get("generated_resume_md", "")
        })

        llm_score = getattr(result, "ats_score", diag["ats_score"])
        final_ats_score = int(diag["ats_score"] * 0.6 + llm_score * 0.4)
        applied_changes = getattr(result, "applied_changes", []) or diag["applied_changes"]

        severity = getattr(result, "severity", "approved" if result.approved else "major")
        target_section = getattr(result, "target_section", None) if not result.approved else None

        return {
            "reviewer_approved": result.approved,
            "reviewer_feedback": result.feedback,
            "review_attempts": attempts + 1,
            "review_severity": severity,
            "patch_section": target_section,
            "patch_instruction": result.feedback if not result.approved else None,
            "diagnostic": {
                "ats_score": final_ats_score,
                "matched_keywords": diag["matched_keywords"],
                "applied_changes": applied_changes,
                "reviewer_summary": result.feedback if result.approved else f"Ajuste sugerido: {result.feedback}"
            }
        }
    except Exception as e:
        print(f"Erro no Quality Reviewer: {e}")
        return {
            "reviewer_approved": False,
            "reviewer_feedback": f"Falha na API de auditoria de qualidade: {e}. Revise o conteúdo manualmente.",
            "review_attempts": MAX_REVIEW_ATTEMPTS,
            "review_severity": "approved",
            "patch_section": None,
            "patch_instruction": None,
            "errors": [f"Revisor de qualidade falhou ({e}); o currículo foi salvo sem revisão automática."],
            "diagnostic": {
                "ats_score": diag["ats_score"],
                "matched_keywords": diag["matched_keywords"],
                "applied_changes": diag["applied_changes"],
                "reviewer_summary": f"Auditoria automática não pôde ser concluída ({e})."
            }
        }

def cover_letter_generator(state: dict) -> dict:
    """
    Gera uma Cover Letter (Carta de Apresentação) personalizada, convincente e alinhada
    com a vaga e o portfólio GitHub, escrita no mesmo idioma da vaga.
    """
    project_items = []
    for r in (state.get("github_repos") or [])[:3]:
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
    repos_summary = "\n".join(project_items) if project_items else "Nenhum repositório específico."
    lang_name = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])["name"]

    system_prompt = (
        "Você é um especialista sênior em redação de cartas de apresentação (Cover Letters) e aconselhamento de carreira.\n"
        f"Escreva uma Cover Letter profissional, elegante e persuasiva inteiramente em {lang_name}, adaptada para a vaga descrita.\n\n"
        "Diretrizes:\n"
        "1. **Abertura**: Saudação formal ao time de recrutamento/gerente de contratação e apresentação com entusiasmo pela vaga.\n"
        "2. **Conexão Técnica & Experiência**: Destaque as principais realizações do candidato pertinentes à vaga, citando experiência prática e projetos reais.\n"
        "3. **Fit Cultural & Valor**: Mostre compreensão dos objetivos da empresa e como o candidato resolverá os desafios propostos.\n"
        "4. **Fechamento**: Conclusão cordial solicitando uma entrevista/conversa técnica.\n"
        "5. **Alinhamento Rigoroso**: NÃO invente informações que não estejam presentes no currículo do candidato.\n"
        "- Retorne APENAS o texto da carta em Markdown limpo, sem cercas de código (```)."
    )

    user_prompt = (
        f"--- VAGA ---\n{_job_context(state)}\n\n"
        f"--- CURRÍCULO DO CANDIDATO ---\n{state.get('generated_resume_md', '')}\n\n"
        f"--- PROJETOS DESTACADOS GITHUB ---\n{repos_summary}"
    )

    try:
        response = _llm(temperature=0.3).invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return {"generated_cover_letter_md": _text(response)}
    except Exception as e:
        print(f"Erro no Cover Letter Generator: {e}")
        return {
            "generated_cover_letter_md": "",
            "errors": [f"Carta de apresentação não foi gerada ({e})."]
        }
