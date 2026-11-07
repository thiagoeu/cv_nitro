"""Agente revisor: auditoria por modelo (Tier 2), snapshot da melhor versão e delegação de validação determinística (Tier 1)."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from src.agents.shared import llm
from src.agents.shared.context import job_context, portfolio_context
from src.agents.shared.sections import LABELS, resolve_section
from src.agents.shared.deterministic_validator import (
    _critical_patch_section,
    _validate_resume_deterministic,
)
from src.agents.prompts.reviewer_prompts import QUALITY_REVIEWER_PROMPT

MAX_REVIEW_ATTEMPTS = 2


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
    interview_tips: List[str] = Field(
        default_factory=list,
        description="Orientações e pontos de atenção estratégicos para a entrevista técnica do candidato com base nos requisitos da vaga."
    )


def quality_reviewer(state: dict) -> dict:
    """
    Revisa o currículo gerado combinando validação determinística Tier 1 (0 tokens)
    com auditoria semântica Tier 2 via LLM para máxima qualidade e eficiência de tokens.
    Classifica falhas em 'minor' (para section_patcher) ou 'major' (para regeneração completa).
    Implementa Snapshot & Rollback da melhor versão avaliada e parada por estagnação.
    """
    attempts = state.get("review_attempts", 0)
    generated_md = state.get("generated_resume_md", "") or ""
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])
    strict = state.get("strict_review", True)

    best_resume = state.get("best_resume_md")
    best_score = state.get("best_ats_score")
    best_diag = state.get("best_diagnostic")

    # Validação determinística preliminar (Tier 1 - zero tokens)
    is_valid, critical_issues, diag = _validate_resume_deterministic(generated_md, state)
    issue_msgs = [msg for msg, _ in critical_issues]

    def build_result_payload(approved: bool, feedback: str, severity: str, final_score: int,
                             applied: list, tips: list, target_sec: Optional[str] = None,
                             final: bool = False) -> dict:
        diagnostic_payload = {
            "ats_score": final_score,
            "matched_keywords": diag["matched_keywords"],
            "missing_keywords": diag["missing_keywords"],
            "curated_repos": diag["curated_repos"],
            "interview_tips": tips or diag["interview_tips"],
            "applied_changes": applied or diag["applied_changes"],
            "reviewer_summary": feedback
        }

        # Gestão de Snapshot da melhor versão válida
        nonlocal best_resume, best_score, best_diag
        updated_best = False
        if is_valid:
            if best_score is None or final_score > best_score:
                best_resume = generated_md
                best_score = final_score
                best_diag = diagnostic_payload
                updated_best = True

        # Critério de parada por estagnação: se não melhorou em relação à melhor versão anterior
        stop_reason = None
        current_md = generated_md
        effective_diag = diagnostic_payload
        kept_current = True

        if approved:
            stop_reason = "target_reached"
        elif attempts > 0 and not updated_best and best_resume is not None:
            # Estagnação de nota: parar para não forçar alucinações e restaurar melhor versão
            stop_reason = "no_improvement"
            current_md = best_resume
            effective_diag = best_diag or diagnostic_payload
            kept_current = False
            feedback = f"Revisão interrompida por estagnação da pontuação ATS. A melhor versão ({best_score}%) foi restaurada automaticamente."
            severity = "approved"
            approved = True
        elif final or attempts + 1 >= MAX_REVIEW_ATTEMPTS:
            stop_reason = "max_attempts"
            if best_resume is not None:
                current_md = best_resume
                effective_diag = best_diag or diagnostic_payload
                kept_current = False
            severity = "approved"

        # Versão mantida ainda com defeito crítico: não aprova e avisa (o snapshot só guarda versões válidas)
        errors = []
        if stop_reason and kept_current and not is_valid:
            approved = False
            stop_reason = "critical_issues_remaining"
            errors = [f"Currículo salvo com pendências críticas, revise antes de enviar: {'; '.join(issue_msgs)}."]

        trace_status = "success" if approved else ("warning" if severity == "minor" else "error")
        trace_entry = {
            "agent": "quality_reviewer",
            "step": f"Auditoria de Qualidade ATS (Tentativa {attempts + 1})",
            "detail": f"Score ATS: {final_score}%. Parecer: {feedback} (Severidade: {severity}).",
            "status": trace_status
        }
        if stop_reason == "no_improvement":
            trace_entry["detail"] += " Restauração automática de snapshot aplicada."

        return {
            "generated_resume_md": current_md,
            "reviewer_approved": approved,
            "reviewer_feedback": feedback,
            "review_attempts": attempts + 1,
            "review_severity": severity,
            "patch_section": target_sec if not approved else None,
            "patch_instruction": feedback if not approved else None,
            "best_resume_md": best_resume,
            "best_ats_score": best_score,
            "best_diagnostic": best_diag,
            "stop_reason": stop_reason,
            "diagnostic": effective_diag,
            "errors": errors,
            "agent_trace": [trace_entry]
        }

    if not is_valid:
        feedback_det = "Ajustes necessários no currículo: " + "; ".join(issue_msgs) + "."
        target_sec = _critical_patch_section(critical_issues)
        if strict:
            return build_result_payload(False, feedback_det, "minor" if target_sec else "major",
                                        diag["ats_score"], diag["applied_changes"], diag["interview_tips"], target_sec)
        # Modo econômico: um único refinamento da seção afetada, sem revisor LLM nem reescrita completa
        if target_sec and attempts == 0:
            return build_result_payload(False, feedback_det, "minor", diag["ats_score"],
                                        diag["applied_changes"], diag["interview_tips"], target_sec)
        return build_result_payload(False, feedback_det, "approved", diag["ats_score"],
                                    diag["applied_changes"], diag["interview_tips"], final=True)

    # Modo econômico (strict_review=False): utiliza apenas o diagnóstico determinístico
    if not strict:
        return build_result_payload(True, "Aprovado em modo econômico com validação estrutural determinística.",
                                    "approved", diag["ats_score"], diag["applied_changes"], diag["interview_tips"])

    # Tier 2: Auditoria semântica fina com LLM apenas se passou no Tier 1
    try:
        structured_llm = llm.chat_model(temperature=0).with_structured_output(ReviewResult)
        result = llm.invoke_tracked(QUALITY_REVIEWER_PROMPT | structured_llm, {
            "language": L["name"],
            "job_context": job_context(state),
            "verified": ", ".join(state.get("verified_technologies") or []) or "Nenhuma informada.",
            "gaps": ", ".join(state.get("unmatched_gaps") or []) or "Nenhuma.",
            "base_resume": state.get("base_resume_md", ""),
            "portfolio_context": portfolio_context(state, 600),
            "generated": state.get("generated_resume_md", "")
        }, generated_md)

        llm_score = getattr(result, "ats_score", diag["ats_score"])
        final_ats_score = int(diag["ats_score"] * 0.6 + llm_score * 0.4)
        if state.get("job_technologies") and state.get("unmatched_gaps"):
            tech_cov = diag.get("tech_coverage", 100) / 100.0
            if tech_cov < 1.0:
                max_allowed = int(round(35 + (50 * tech_cov)))
                final_ats_score = min(final_ats_score, max_allowed)
        applied_changes = getattr(result, "applied_changes", []) or diag["applied_changes"]
        interview_tips = getattr(result, "interview_tips", []) or diag["interview_tips"]

        severity = getattr(result, "severity", "approved" if result.approved else "major")
        target_section = getattr(result, "target_section", None) if not result.approved else None
        if severity == "minor":
            # Patch numa seção inexistente não altera nada: sem título real, regenera
            target_section = resolve_section(generated_md, target_section, L)
            if not target_section:
                severity = "major"

        return build_result_payload(
            result.approved,
            result.feedback if result.approved else f"Ajuste sugerido: {result.feedback}",
            severity,
            final_ats_score,
            applied_changes,
            interview_tips,
            target_section
        )
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
                "missing_keywords": diag["missing_keywords"],
                "curated_repos": diag["curated_repos"],
                "interview_tips": diag["interview_tips"],
                "applied_changes": diag["applied_changes"],
                "reviewer_summary": f"Auditoria automática não pôde ser concluída ({e})."
            },
            "agent_trace": [{
                "agent": "quality_reviewer",
                "step": "Auditoria de Qualidade ATS",
                "detail": f"Falha na API de auditoria ({e}). O currículo prosseguiu com avaliação determinística.",
                "status": "warning"
            }]
        }
