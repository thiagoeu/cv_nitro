"""Agentes de redação: currículo completo, refinamento de uma seção e carta de apresentação."""
from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.shared import llm
from src.agents.shared.context import (
    job_context,
    portfolio_context,
    format_repos_summary,
    resolve_verified_and_gaps,
)
from src.agents.shared.sections import LABELS, splice_markdown_section, unfilled_placeholders
from src.agents.prompts.writer_prompts import (
    build_resume_system_prompt,
    build_resume_user_messages,
    SECTION_PATCH_PROMPT,
    build_cover_letter_prompts,
)


def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown com formatação de alta fidelidade e aderência ATS,
    no idioma da vaga (traduzindo o currículo base), com tabela de habilidades e bullets de impacto.
    Uma única chamada: os extratos higienizados dos READMEs (top 3) vão direto no prompt.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = job_context(state)
    feedback = state.get("reviewer_feedback", "")
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])
    portfolio = portfolio_context(state, 1200) or "Nenhum repositório do GitHub fornecido."

    verified_techs, gaps = resolve_verified_and_gaps(state)
    verified_str = ", ".join(verified_techs) if verified_techs else "Utilize apenas as tecnologias do currículo base."
    gaps_str = ", ".join(gaps) if gaps else "Nenhuma pendência identificada."

    system_prompt = build_resume_system_prompt(L, verified_str, gaps_str)
    messages = build_resume_user_messages(
        system_prompt=system_prompt,
        base_resume=base_resume,
        job_desc=job_desc,
        verified_str=verified_str,
        gaps_str=gaps_str,
        portfolio=portfolio,
        feedback=feedback,
    )

    response = llm.invoke_tracked(
        llm.chat_model(temperature=0.2, thinking_level=None),
        messages,
        f"{system_prompt}\n{base_resume}\n{job_desc}\n{portfolio}",
    )
    generated_text = llm.response_text(response)
    return {
        "generated_resume_md": generated_text,
        "generation_truncated": llm.is_truncated(response),
        "agent_trace": [{
            "agent": "resume_generator",
            "step": "Redação Executiva ATS",
            "detail": f"Currículo gerado integralmente em {L['name']} com tabela de habilidades e verbos em 1ª pessoa.",
            "status": "success"
        }]
    }


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

    try:
        formatted_prompt = SECTION_PATCH_PROMPT.format(
            target_section=target_section,
            instruction=instruction,
            current_resume=current_resume,
            language=L["name"],
        )
        response = llm.invoke_tracked(
            llm.chat_model(temperature=0.2, thinking_level="low"),
            formatted_prompt,
            formatted_prompt,
        )
        patched_section_md = llm.response_text(response)
        updated_resume = splice_markdown_section(current_resume, target_section, patched_section_md)
        return {
            "generated_resume_md": updated_resume,
            "generation_truncated": bool(state.get("generation_truncated")) or llm.is_truncated(response),
            "agent_trace": [{
                "agent": "section_patcher",
                "step": "Refinamento Cirúrgico de Seção",
                "detail": f"Seção '{target_section}' reescrita cirurgicamente e reenxertada sem refazer o currículo inteiro.",
                "status": "success"
            }]
        }
    except Exception as e:
        print(f"Erro no section_patcher: {e}")
        return {
            "generated_resume_md": current_resume,
            "errors": [f"Falha no patch cirúrgico: {e}"],
            "agent_trace": [{
                "agent": "section_patcher",
                "step": "Refinamento Cirúrgico de Seção",
                "detail": f"Falha no patch cirúrgico: {e}",
                "status": "error"
            }]
        }


def cover_letter_generator(state: dict) -> dict:
    """
    Gera uma Cover Letter (Carta de Apresentação) personalizada, convincente e alinhada
    com a vaga e o portfólio GitHub, escrita no mesmo idioma da vaga.
    """
    repos_summary = format_repos_summary(state.get("github_repos") or [], max_repos=3)
    lang_name = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])["name"]
    verified_str = ", ".join(state.get("verified_technologies") or []) or "Nenhuma informada."
    gaps_str = ", ".join(state.get("unmatched_gaps") or []) or "Nenhuma."

    system_prompt, user_prompt = build_cover_letter_prompts(
        lang_name=lang_name,
        job_desc=job_context(state),
        generated_resume=state.get("generated_resume_md", ""),
        repos_summary=repos_summary,
        verified_str=verified_str,
        gaps_str=gaps_str,
    )

    try:
        response = llm.invoke_tracked(
            llm.chat_model(temperature=0.3),
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ],
            f"{system_prompt}\n{user_prompt}",
        )
        letter = llm.response_text(response)
        unfilled = [m.group() for m in unfilled_placeholders(letter)]
        return {
            "generated_cover_letter_md": letter,
            "errors": [f"A carta de apresentação tem marcadores não preenchidos ({', '.join(unfilled[:3])}); revise antes de enviar."] if unfilled else [],
            "agent_trace": [{
                "agent": "cover_letter_generator",
                "step": "Redação da Carta de Apresentação",
                "detail": f"Carta de apresentação em 4 atos estruturada em {lang_name} com base nos projetos do portfólio.",
                "status": "success"
            }]
        }
    except Exception as e:
        print(f"Erro no Cover Letter Generator: {e}")
        return {
            "generated_cover_letter_md": "",
            "errors": [f"Carta de apresentação não foi gerada ({e})."],
            "agent_trace": [{
                "agent": "cover_letter_generator",
                "step": "Redação da Carta de Apresentação",
                "detail": f"Carta não gerada devido a falha na API ({e}).",
                "status": "warning"
            }]
        }
