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
    # O gerador com thinking padrão já levou ~150s numa chamada: 300s dá folga sem esperar para sempre.
    def make(model: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, timeout=300, max_retries=2, **extra)
    fallbacks = []
    if config.GEMINI_FALLBACK_MODEL and config.GEMINI_FALLBACK_MODEL != config.GEMINI_MODEL:
        fallbacks.append(make(config.GEMINI_FALLBACK_MODEL))
    if config.GROQ_API_KEY:
        # Tokens de raciocínio contam no limite por minuto do Groq; só o gpt-oss aceita "low".
        groq_extra = {"reasoning_effort": thinking_level} if thinking_level and config.GROQ_MODEL.startswith("openai/gpt-oss") else {}
        fallbacks.append(ChatGroq(model=config.GROQ_MODEL, temperature=temperature, timeout=300, max_retries=2, **groq_extra))
    if not fallbacks:
        return make(config.GEMINI_MODEL)
    # Cadeia plana (with_fallbacks aninhado perde os reservas no with_structured_output).
    # Qualquer erro troca de modelo: a cota 429 do free tier do Gemini é por modelo e estoura rápido.
    return make(config.GEMINI_MODEL).with_fallbacks(fallbacks)

def _text(response) -> str:
    """Gemini 3.x devolve `content` como lista de blocos; `.text` junta só o texto. Remove cercas ```markdown."""
    text = response.text.strip()
    return re.sub(r"^```(?:markdown|md)?\s*\n(.*?)\n?```$", r"\1", text, flags=re.DOTALL).strip()

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

def github_researcher(state: dict) -> dict:
    """
    Busca repositórios públicos do usuário no GitHub e extrai READMEs 
    dos repositórios que tenham as linguagens/tecnologias buscadas pela vaga.
    """
    username = (state.get("github_username") or "").strip()
    technologies = [t.lower() for t in state.get("job_technologies", [])]
    
    if not username:
        return {"github_repos": [], "github_readmes": {}}

    # Validação do nome de usuário do GitHub (alfanumérico com hifens simples internos, max 39 chars)
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
        print(f"Nome de usuário GitHub inválido ou potencialmente inseguro: '{username}'")
        return {"github_repos": [], "github_readmes": {}}
        
    headers = {}
    token = config.GITHUB_TOKEN
    if token and "your_github_token_here" not in token:
        headers["Authorization"] = f"Bearer {token}"
        
    repos_url = f"https://api.github.com/users/{username}/repos?type=public&sort=updated&per_page=30"
    request_timeout = (5.0, 10.0)
    
    try:
        response = requests.get(repos_url, headers=headers, timeout=request_timeout)
        if response.status_code != 200:
            print(f"Erro ao acessar GitHub: {response.status_code}")
            return {"github_repos": [], "github_readmes": {}}
            
        repos = response.json()
        selected_repos = []
        readmes = {}
        
        # Filtra os repositórios mais promissores
        for repo in repos:
            repo_lang = (repo.get("language") or "").lower()
            
            if not technologies or repo_lang in technologies or any(t in str(repo.get("description", "")).lower() for t in technologies):
                selected_repos.append({
                    "name": repo["name"],
                    "description": repo.get("description", ""),
                    "language": repo.get("language"),
                    "url": repo["html_url"],
                    "default_branch": repo["default_branch"]
                })
                
                if len(selected_repos) >= 3:
                    break
                    
        for repo in selected_repos:
            repo_name = repo["name"]
            # Validação do nome do repositório para evitar path traversal ou caracteres de controle
            if not re.match(r"^[a-zA-Z0-9_.-]+$", repo_name):
                continue
                
            readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
            try:
                readme_resp = requests.get(readme_url, headers=headers, timeout=request_timeout)
                if readme_resp.status_code == 200:
                    content_b64 = readme_resp.json().get("content", "")
                    content_str = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                    readmes[repo_name] = content_str
            except Exception as e:
                print(f"Erro ao baixar README de {repo_name}: {e}")
                
        return {
            "github_repos": selected_repos,
            "github_readmes": readmes
        }
        
    except Exception as e:
        print(f"Erro no GitHub Researcher: {e}")
        return {"github_repos": [], "github_readmes": {}}

def _portfolio_context(state: dict, readme_chars: int) -> str:
    context = ""
    readmes = state.get("github_readmes", {})
    for repo in state.get("github_repos", []):
        name = repo["name"]
        context += (
            f"\n### Repositório: {name}\nURL: {repo.get('url', '')}\nLinguagem: {repo.get('language', '')}\n"
            f"Descrição: {repo.get('description', '')}\nREADME:\n{readmes.get(name, '')[:readme_chars]}\n"
        )
    return context

def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown com formatação de alta fidelidade e aderência ATS,
    no idioma da vaga (traduzindo o currículo base), com tabela de habilidades e bullets de impacto.
    Falhas do modelo são propagadas para o app não salvar o currículo base como se fosse otimizado.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = _job_context(state)
    feedback = state.get("reviewer_feedback", "")
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])

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
- **<Tópico de impacto>:** <verbo de ação forte + escopo + resultado mensurável ou de escala>

(3 a 5 bullets por experiência, cobrindo impacto, back-end/arquitetura, front-end, dados/integrações e processos, quando aplicável.)

## {L['projects']}
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação>
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
6. Retorne APENAS o Markdown do currículo, sem comentários e sem cercas de código (```)."""

    if feedback:
        system_prompt += f"\n\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. Ajuste o currículo rigorosamente conforme esse feedback."

    user_prompt = (
        f"--- VAGA ---\n{job_desc}\n\n"
        f"--- CURRÍCULO BASE ---\n{base_resume}\n\n"
        f"--- PORTFÓLIO GITHUB ---\n{_portfolio_context(state, 400)}"
    )

    # Etapa de qualidade: mantém o thinking padrão do modelo.
    response = _llm(temperature=0.2, thinking_level=None).invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    return {"generated_resume_md": _text(response)}

class ReviewResult(BaseModel):
    approved: bool = Field(description="True se o currículo não tiver alucinações, estiver todo no idioma pedido e seguir o padrão estrutural; False caso contrário.")
    feedback: str = Field(description="Feedback detalhado explicando o que foi corrigido ou aprovado.")
    ats_score: int = Field(default=85, description="Nota de compatibilidade ATS de 0 a 100.")
    applied_changes: List[str] = Field(default_factory=list, description="Lista com 3 a 5 melhorias ou adequações realizadas.")

def quality_reviewer(state: dict) -> dict:
    """
    Revisa o currículo gerado para garantir conformidade estrutural, idioma da vaga,
    ausência de informações técnicas ou cargos inventados, e gera diagnóstico ATS.
    """
    attempts = state.get("review_attempts", 0)

    # Identifica correspondência de termos técnicos e keywords no currículo gerado
    generated_md = state.get("generated_resume_md", "") or ""
    all_terms = (state.get("job_keywords") or []) + (state.get("job_technologies") or [])
    gen_lower = generated_md.lower()
    matched = [t for t in all_terms if t.lower() in gen_lower]
    seen = set()
    unique_matched = []
    for m in matched:
        if m.lower() not in seen:
            seen.add(m.lower())
            unique_matched.append(m)

    # Se modo econômico ativado (strict_review=False), ignora chamada de LLM adicional
    if not state.get("strict_review", True):
        match_ratio = len(unique_matched) / max(len(all_terms), 1)
        estimated_score = min(98, max(75, int(70 + match_ratio * 25)))
        return {
            "reviewer_approved": True,
            "reviewer_feedback": "Aprovado em modo econômico de tokens.",
            "review_attempts": attempts + 1,
            "diagnostic": {
                "ats_score": estimated_score,
                "matched_keywords": unique_matched,
                "applied_changes": [
                    "Estrutura executiva em Markdown de alta fidelidade aplicada",
                    f"Incorporação de {len(unique_matched)} termos e tecnologias da vaga",
                    "Tabela de habilidades técnicas padronizada em 2 colunas"
                ],
                "reviewer_summary": "Currículo validado rapidamente em modo econômico com foco em termos ATS."
            }
        }

    if attempts >= MAX_REVIEW_ATTEMPTS:
        return {
            "reviewer_approved": False,
            "reviewer_feedback": "Limite de tentativas de revisão atingido. Prosseguindo com versão atual.",
            "review_attempts": attempts + 1,
            "diagnostic": {
                "ats_score": 80,
                "matched_keywords": unique_matched,
                "applied_changes": ["Currículo adaptado para a vaga alvo"],
                "reviewer_summary": "Limite de revisões atingido; versão preservada para o usuário."
            }
        }

    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])
    try:
        structured_llm = _llm(temperature=0).with_structured_output(ReviewResult)
        prompt = PromptTemplate.from_template(
            "Você é um auditor rigoroso de currículos técnicos de alto padrão e compatibilidade ATS.\n"
            "Avalie o currículo gerado segundo os critérios:\n"
            "1. **Alucinações:** o currículo cita empregos, tecnologias ou ferramentas que NÃO constam no currículo base nem nos READMEs?\n"
            "2. **Idioma:** o currículo está INTEIRAMENTE em {language} (títulos, tabela, bullets, cargos, formação, idiomas)?\n"
            "3. **Layout:** a seção de habilidades é uma tabela Markdown de 2 colunas com linha separadora, "
            "e os bullets seguem o formato `- **Tópico:** ação` (sem colchetes)?\n\n"
            "Avalie a qualidade ATS:\n"
            "- Atribua um ats_score de 0 a 100 baseado na fidelidade, clareza e densidade das keywords.\n"
            "- Liste em applied_changes de 3 a 5 adequações realizadas em relação ao currículo base.\n\n"
            "--- CURRÍCULO BASE ---\n{base_resume}\n\n"
            "--- READMEs FORNECIDOS ---\n{portfolio_context}\n\n"
            "--- CURRÍCULO GERADO (Para revisão) ---\n{generated}\n\n"
            "Retorne aprovado (True) se estiver tudo correto, ou (False) se houver problemas, explicando no feedback o que corrigir."
        )
        result = (prompt | structured_llm).invoke({
            "language": L["name"],
            "base_resume": state.get("base_resume_md", ""),
            "portfolio_context": _portfolio_context(state, 300),
            "generated": state.get("generated_resume_md", "")
        })

        ats_score = getattr(result, "ats_score", 85)
        applied_changes = getattr(result, "applied_changes", []) or [
            "Reestruturação de habilidades técnicas em tabela de 2 colunas",
            f"Alinhamento de {len(unique_matched)} tecnologias e conceitos da vaga",
            "Bullets reescritos com verbos de ação e foco em impacto"
        ]

        return {
            "reviewer_approved": result.approved,
            "reviewer_feedback": result.feedback,
            "review_attempts": attempts + 1,
            "diagnostic": {
                "ats_score": ats_score,
                "matched_keywords": unique_matched,
                "applied_changes": applied_changes,
                "reviewer_summary": result.feedback if result.approved else f"Ajuste sugerido: {result.feedback}"
            }
        }
    except Exception as e:
        print(f"Erro no Quality Reviewer: {e}")
        # Não aprova, mas encerra o loop: regenerar com "a API falhou" como feedback não melhora nada.
        return {
            "reviewer_approved": False,
            "reviewer_feedback": f"Falha na API de auditoria de qualidade: {e}. Revise o conteúdo manualmente.",
            "review_attempts": MAX_REVIEW_ATTEMPTS,
            "errors": [f"Revisor de qualidade falhou ({e}); o currículo foi salvo sem revisão automática."],
            "diagnostic": {
                "ats_score": 75,
                "matched_keywords": unique_matched,
                "applied_changes": ["Currículo otimizado com base na descrição da vaga"],
                "reviewer_summary": f"Auditoria automática não pôde ser concluída ({e})."
            }
        }

def cover_letter_generator(state: dict) -> dict:
    """
    Gera uma Cover Letter (Carta de Apresentação) personalizada, convincente e alinhada
    com a vaga e o portfólio GitHub, escrita no mesmo idioma da vaga.
    """
    repos_summary = ", ".join([r.get("name", "") for r in state.get("github_repos", []) if r.get("name")])
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
