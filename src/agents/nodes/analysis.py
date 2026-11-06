"""Agentes de análise: requisitos da vaga e mapeamento de competências comprovadas."""
import os
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


class CompetencyAudit(BaseModel):
    verified_technologies: List[str] = Field(
        description="Tecnologias exigidas pela vaga que o candidato comprovadamente domina (seja por citação direta ou por frameworks/ecossistemas correlatos, ex.: Expo comprova React Native, NestJS comprova Node.js, Postgres comprova SQL)."
    )
    unmatched_gaps: List[str] = Field(
        description="Tecnologias exigidas pela vaga que NÃO possuem respaldo no currículo base nem nos repositórios do GitHub do candidato (gaps reais, ex.: Java se não houver Java em nenhum lugar)."
    )
    reasoning: str = Field(description="Explicação concisa do cruzamento semântico.")


COMPETENCY_PROMPT = PromptTemplate.from_template(
    "Você é um especialista em auditoria técnica de competências e compatibilidade de vagas de tecnologia.\n"
    "Sua missão é cruzar as tecnologias exigidas pela vaga com o perfil real do candidato (currículo base e portfólio no GitHub) "
    "e classificar com inteligência semântica e honestidade estrita:\n\n"
    "DIRETRIZES DE AUDITORIA:\n"
    "1. **Reconhecimento Semântico Amplo:** Reconheça ferramentas, frameworks, ecossistemas e sinônimos legítimos de mercado. "
    "Por exemplo: Expo comprova React Native; NestJS e Express comprovam Node.js; PostgreSQL, MySQL e SQLite comprovam SQL; "
    "TypeORM e Prisma comprovam ORM/bancos relacionais; Docker Compose comprova Docker; RAG, Ollama e LLMs comprovam IA Generativa; etc.\n"
    "2. **HONESTIDADE E TRAVA FACTUAL (NÃO INVENTE):** Se o candidato NÃO possui experiência nem projetos com a tecnologia "
    "(ex.: Java, C#, Flutter, Kubernetes) e ela não é respaldada por nenhuma ferramenta equivalente do perfil, "
    "coloque-a OBRIGATORIAMENTE em 'unmatched_gaps'. Jamais suponha competências sem evidência textual ou prática!\n\n"
    "--- VAGA ALVO ---\n"
    "Cargo: {job_title}\n"
    "Tecnologias exigidas: {job_technologies}\n\n"
    "--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}\n\n"
    "--- REPOSITÓRIOS GITHUB DO CANDIDATO ---\n{github_repos_summary}\n\n"
    "Retorne a análise estruturada."
)


def competency_matcher(state: dict) -> dict:
    """
    Agente Semântico de Competências (Grounded Semantic Matcher):
    Cruza via LLM os requisitos da vaga contra o currículo base e o portfólio GitHub,
    reconhecendo frameworks correlatos (ex.: Expo -> React Native) sem depender de dicionários rígidos,
    mas com trava factual estrita para não inventar o que o candidato não tem (ex.: Java -> Gap).
    Possui fallback automático para o validador determinístico.
    """
    job_technologies = state.get("job_technologies", [])
    if not job_technologies:
        return {
            "verified_technologies": [],
            "unmatched_gaps": [],
            "agent_trace": [{
                "agent": "competency_matcher",
                "step": "Mapeamento Semântico de Competências",
                "detail": "Nenhuma tecnologia exigida identificada para auditoria.",
                "status": "info"
            }]
        }

    base_resume = state.get("base_resume_md", "")
    all_repos = state.get("raw_github_repos", []) or state.get("github_repos", []) or []
    readmes = state.get("github_readmes") or {}

    repo_lines = []
    for r in all_repos[:30]:
        if r.get("fork", False):
            continue
        name = r.get("name") or ""
        lang = r.get("language") or "Multi-stack"
        topics = r.get("topics") or []
        desc = r.get("description") or ""
        topic_str = f" [tags: {', '.join(topics)}]" if topics else ""
        repo_lines.append(f"- **{name}** ({lang}){topic_str}: {desc}")

    for repo_name, r_content in readmes.items():
        if r_content:
            clean_snippet = " ".join(str(r_content).split()[:40])
            repo_lines.append(f"- README ({repo_name}): {clean_snippet}")

    repos_summary = "\n".join(repo_lines) if repo_lines else "Nenhum repositório público fornecido."

    strict_review = state.get("strict_review", True)
    is_mocked = hasattr(llm.chat_model, "mock_calls") or hasattr(llm.chat_model, "return_value")
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not strict_review or (api_key == "dummy" and not is_mocked):
        res = competency_matcher_core.classify_competencies(job_technologies, base_resume, all_repos, readmes)
        verified = res["verified_technologies"]
        gaps = res["unmatched_gaps"]
        detail = (
            f"Mapeamento de competências (modo determinístico): {len(verified)} comprovadas e "
            f"{len(gaps)} pendências ({res['match_rate']}% aderência)."
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

    try:
        structured_llm = llm.chat_model(temperature=0).with_structured_output(CompetencyAudit)
        chain = COMPETENCY_PROMPT | structured_llm
        payload = {
            "job_title": state.get("job_title", ""),
            "job_technologies": ", ".join(job_technologies),
            "base_resume": base_resume,
            "github_repos_summary": repos_summary,
        }
        prompt_txt = COMPETENCY_PROMPT.format(**payload)
        audit_res = llm.invoke_tracked(chain, payload, prompt_txt)

        verified = [t for t in (audit_res.verified_technologies or []) if t in job_technologies]
        for v in (audit_res.verified_technologies or []):
            if v not in verified:
                verified.append(v)

        gaps = [g for g in (audit_res.unmatched_gaps or []) if g not in verified]
        for t in job_technologies:
            if t not in verified and t not in gaps:
                gaps.append(t)

        reasoning = getattr(audit_res, "reasoning", "")
        detail = (
            f"Auditoria semântica via Agente LLM: {len(verified)} tecnologias comprovadas e "
            f"{len(gaps)} pendências técnicas reais."
        )
        status = "success"
    except Exception as e:
        print(f"Fallback no competency_matcher para modo determinístico: {e}")
        res = competency_matcher_core.classify_competencies(job_technologies, base_resume, all_repos, state.get("github_readmes"))
        verified = res["verified_technologies"]
        gaps = res["unmatched_gaps"]
        detail = f"Fallback determinístico aplicado ({e}): {len(verified)} comprovadas, {len(gaps)} pendências."
        status = "warning"

    return {
        "verified_technologies": verified,
        "unmatched_gaps": gaps,
        "agent_trace": [{
            "agent": "competency_matcher",
            "step": "Mapeamento Semântico de Competências",
            "detail": detail,
            "status": status,
        }],
    }
