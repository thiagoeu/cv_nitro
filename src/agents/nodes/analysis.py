"""Agentes de análise: requisitos da vaga e mapeamento de competências comprovadas."""
from typing import List, Literal
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.agents.shared import llm
from src.core import competency_matcher as competency_matcher_core

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
        return {
            "job_keywords": [], "job_technologies": [], "job_language": "pt", "job_summary": "",
            "agent_trace": [{
                "agent": "job_analyzer",
                "step": "Análise de Vaga",
                "detail": "Descrição da vaga vazia recebida.",
                "status": "warning"
            }]
        }

    structured_llm = llm.chat_model(temperature=0).with_structured_output(JobAnalysis)
    prompt = PromptTemplate.from_template(
        "Você é um recrutador especialista. Analise a seguinte vaga de emprego "
        "e extraia as principais tecnologias, palavras-chave comportamentais/conceituais "
        "e identifique o idioma em que a vaga está escrita. Ignore textos de interface do site "
        "de vagas (ex.: 'Sobre a vaga', 'Candidatar-se') ao decidir o idioma. "
        "Escreva também um resumo enxuto da vaga, que substituirá o texto original nas próximas etapas.\n\n"
        "Vaga:\n{job_description}"
    )
    result = llm.invoke_tracked(prompt | structured_llm, {"job_description": job_description}, job_description)

    return {
        "job_keywords": result.keywords,
        "job_technologies": result.technologies,
        "job_language": result.language,
        "job_summary": result.summary,
        "agent_trace": [{
            "agent": "job_analyzer",
            "step": "Análise de Requisitos e Idioma",
            "detail": f"Detectado idioma '{result.language}'. Identificadas {len(result.technologies)} tecnologias e {len(result.keywords)} palavras-chave ATS.",
            "status": "success"
        }]
    }


def job_context(state: dict) -> str:
    """Resumo da vaga + termos ATS no lugar do texto colado: corta boilerplate (benefícios, institucional) de cada chamada seguinte."""
    summary = state.get("job_summary")
    if not summary:
        return state.get("job_description", "")
    terms = ", ".join(dict.fromkeys((state.get("job_technologies") or []) + (state.get("job_keywords") or [])))
    return f"{summary}\n\nPalavras-chave ATS: {terms}"


def competency_matcher(state: dict) -> dict:
    """
    Agente / Nó de Mapeamento Semântico de Competências:
    Compara os requisitos extraídos da vaga contra o currículo base e o portfólio do GitHub
    usando equivalências semânticas e canônicas legítimas de mercado (ex.: HTML5 -> HTML, PostgreSQL -> SQL).
    Separa em:
    - verified_technologies: tecnologias que o candidato comprovou e podem figurar no currículo.
    - unmatched_gaps: pendências técnicas reais que o candidato NÃO possui (proibidas no histórico).
    """
    job_technologies = state.get("job_technologies", [])
    base_resume = state.get("base_resume_md", "")
    repos = state.get("github_repos", []) or state.get("raw_github_repos", []) or []

    res = competency_matcher_core.classify_competencies(job_technologies, base_resume, repos, state.get("github_readmes"))
    verified = res["verified_technologies"]
    gaps = res["unmatched_gaps"]

    detail = (
        f"Mapeadas {len(verified)} tecnologias comprovadas/equivalentes e "
        f"{len(gaps)} pendências técnicas reais ({res['match_rate']}% de aderência inicial comprovada)."
    )

    return {
        "verified_technologies": verified,
        "unmatched_gaps": gaps,
        "agent_trace": [{
            "agent": "competency_matcher",
            "step": "Mapeamento Semântico de Competências",
            "detail": detail,
            "status": "success",
        }],
    }
