"""Agente revisor: validação determinística (Tier 1), auditoria por modelo (Tier 2) e snapshot da melhor versão."""
import re
from typing import List, Literal, Optional
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.agents.shared import llm
from src.agents.nodes.analysis import job_context
from src.agents.nodes.github import portfolio_context
from src.agents.shared.sections import LABELS, resolve_section, section_of, unfilled_placeholders
from src.core import competency_matcher as competency_matcher_core

MAX_REVIEW_ATTEMPTS = 2


def _critical_patch_section(critical_issues: list) -> Optional[str]:
    """Seção do primeiro defeito crítico localizável; None quando nenhum está dentro de uma seção (ex.: título do cargo)."""
    return next((section for _, section in critical_issues if section), None)


def _validate_resume_deterministic(generated_md: str, state: dict) -> tuple[bool, list[tuple[str, Optional[str]]], dict]:
    """
    Auditoria determinística Tier 1 (0 tokens de LLM):
    1. Placeholders residuais (<Nome>, <Empresa>, etc.) - Crítico
    2. Integridade de URLs de repositórios citados vs repositórios obtidos do GitHub - Crítico
    3. Conformidade da tabela de habilidades (aviso e cálculo estrutural)
    4. Mapeamento real de termos da vaga e cálculo auditável de ATS (0 a 100, linear)
    Defeitos críticos saem como (mensagem, seção onde está o defeito ou None).
    """
    critical_issues = []
    warnings = []
    generated_md = generated_md or ""

    # 1. Placeholders residuais: detecta padrões como <Nome>, <Cargo alvo...>, <Cidade, UF>
    # Excetua endereços de e-mail no formato <usuario@dominio.com>
    unfilled = [m.group() for m in unfilled_placeholders(generated_md)]
    if unfilled:
        sample = ", ".join(unfilled[:3])
        critical_issues.append((f"O currículo contém marcadores de preenchimento não substituídos: {sample}",
                                section_of(generated_md, lambda body: bool(unfilled_placeholders(body)))))

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
            critical_issues.append((f"O repositório citado '{raw_url}' não consta no portfólio retornado pela API do GitHub",
                                    section_of(generated_md, lambda body, u=raw_url: u in body)))

    # Resolução de contexto do candidato e competências classificadas
    job_technologies = [t.strip() for t in (state.get("job_technologies") or []) if t and t.strip()]
    job_keywords = [k.strip() for k in (state.get("job_keywords") or []) if k and k.strip()]
    repos = state.get("github_repos", []) or state.get("raw_github_repos", []) or []
    candidate_bg = competency_matcher_core.candidate_evidence(state.get("base_resume_md", ""), repos, state.get("github_readmes"))

    unmatched_gaps = state.get("unmatched_gaps") or []
    verified_techs = state.get("verified_technologies") or []
    unmatched_gaps_lower = {g.lower() for g in unmatched_gaps}
    verified_techs_lower = {v.lower() for v in verified_techs}

    # 2.1 Trava factual: verificar se alguma pendência técnica não comprovada foi inserida
    if unmatched_gaps:
        for gap in unmatched_gaps:
            if competency_matcher_core.matches_technology(gap, generated_md) and not competency_matcher_core.matches_technology(gap, candidate_bg):
                critical_issues.append((f"Violação de trava factual: O termo de pendência '{gap}' foi atribuído indevidamente ao histórico.",
                                        section_of(generated_md, lambda body, g=gap: competency_matcher_core.matches_technology(g, body))))

    # 2.2 Currículo vazio ou cortado pelo limite de saída do modelo (sem seção a refinar)
    if not generated_md.strip():
        critical_issues.append(("O currículo gerado está vazio", None))
    if state.get("generation_truncated"):
        critical_issues.append(("A geração foi interrompida pelo limite de saída do modelo e o currículo está incompleto", None))

    # 3. Tabela Markdown de habilidades com 2 colunas
    has_table = bool(re.search(r"\|\s*:?---+\s*\|\s*:?---+\s*\|", generated_md))
    if not has_table:
        warnings.append("A seção de habilidades deve conter uma tabela Markdown de 2 colunas com o separador '| :--- | :--- |'")

    # 4. Mapeamento de termos ATS e pontuação auditável
    # A tecnologia só é considerada matched se NÃO for uma pendência técnica (unmatched_gaps) E constar no currículo gerado
    matched_techs = []
    for t in job_technologies:
        if t.lower() in unmatched_gaps_lower:
            continue
        if competency_matcher_core.matches_technology(t, generated_md):
            matched_techs.append(t)

    matched_kws = []
    for k in job_keywords:
        if k.lower() in unmatched_gaps_lower:
            continue
        if competency_matcher_core.matches_technology(k, generated_md):
            matched_kws.append(k)

    seen = set()
    unique_matched = []
    for m in (matched_techs + matched_kws):
        if m.lower() not in seen and m.lower() not in unmatched_gaps_lower:
            seen.add(m.lower())
            unique_matched.append(m)

    # Identificação determinística de lacunas técnicas e conceituais (Gaps reais da vaga)
    matched_techs_lower = {t.lower() for t in matched_techs}
    matched_kws_lower = {k.lower() for k in matched_kws}
    missing_techs = [t for t in job_technologies if t.lower() not in matched_techs_lower]
    missing_kws = [k for k in job_keywords if k.lower() not in matched_kws_lower]

    missing_keywords = []
    missing_seen = set()
    # Prioritariamente inclui todas as pendências técnicas reais
    for gap in (unmatched_gaps or []):
        if gap.lower() not in missing_seen:
            missing_seen.add(gap.lower())
            missing_keywords.append(gap)

    for m in (missing_techs + missing_kws):
        if m.lower() not in missing_seen and m.lower() not in seen:
            missing_seen.add(m.lower())
            missing_keywords.append(m)

    tech_rate = len(matched_techs) / max(len(job_technologies), 1)
    keyword_rate = len(matched_kws) / max(len(job_keywords), 1)
    structural_penalties = (len(critical_issues) * 0.25) + (0.20 if not has_table else 0.0)
    structural_rate = max(0.4, 1.0 - structural_penalties)

    base_score = (0.50 * tech_rate) + (0.25 * keyword_rate) + (0.25 * structural_rate)
    ats_score = int(min(100, max(0, round(base_score * 100))))

    # Trava de honestidade ATS: se há pendências técnicas fundamentais na vaga,
    # o score ATS não pode atingir notas de excelência/100%. É limitado proporcionalmente.
    if job_technologies and len(missing_techs) > 0 and len(unmatched_gaps) > 0:
        max_allowed_score = int(round(35 + (50 * tech_rate)))
        ats_score = min(ats_score, max_allowed_score)

    applied_changes = [
        f"Alinhamento comprovado de {len(matched_techs)} tecnologias da vaga no histórico",
        f"Integração natural de {len(matched_kws)} palavras-chave conceituais/ATS",
        "Formatação de habilidades técnicas em tabela padronizada de 2 colunas" if has_table else "Estrutura executiva em tópicos aplicada",
        "Experiências reescritas com foco em impacto e verbos de ação"
    ]

    # Repositórios curados pelo relevance_ranker com seus scores
    curated_repos = []
    for r in state.get("github_repos", []) or []:
        curated_repos.append({
            "name": r.get("name", ""),
            "language": r.get("language", ""),
            "url": r.get("url", ""),
            "relevance_score": r.get("relevance_score", 0.0)
        })

    # Roteiro determinístico de preparação para entrevista baseado nos gaps e projetos
    deterministic_interview_tips = []
    if missing_keywords:
        top_missing = ", ".join(missing_keywords[:4])
        deterministic_interview_tips.append(
            f"Como abordar requisitos em aberto: Esteja preparado para demonstrar capacidade de aprendizado rápido nas tecnologias não evidenciadas no currículo ({top_missing}), citando fundamentos sólidos em stacks correlatas."
        )
    if curated_repos:
        repo_names = ", ".join(r["name"] for r in curated_repos[:2] if r["name"])
        deterministic_interview_tips.append(
            f"Projetos a destacar na entrevista: Use como exemplos práticos os projetos {repo_names}, detalhando as decisões arquiteturais e resolução de problemas técnicos."
        )
    if not deterministic_interview_tips:
        deterministic_interview_tips.append(
            "Conexão técnica: Destaque sua trajetória enfatizando resultados mensuráveis e o impacto direto gerado nas experiências anteriores."
        )

    is_valid = len(critical_issues) == 0
    diagnostic_data = {
        "ats_score": ats_score,
        "matched_keywords": unique_matched,
        "missing_keywords": missing_keywords,
        "curated_repos": curated_repos,
        "interview_tips": deterministic_interview_tips,
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
        prompt = PromptTemplate.from_template(
            "Você é um auditor rigoroso de currículos técnicos de alto padrão e compatibilidade ATS.\n"
            "Avalie o currículo gerado segundo os critérios:\n"
            "1. **Alucinações:** o currículo cita empregos, tecnologias ou ferramentas que NÃO constam no currículo base nem nos READMEs?\n"
            "2. **Idioma:** o currículo está INTEIRAMENTE em {language} (títulos, tabela, bullets, cargos, formação, idiomas)?\n"
            "3. **Layout:** a seção de habilidades é uma tabela Markdown de 2 colunas com linha separadora, "
            "e os bullets seguem o formato `- **Tópico:** ação` (sem colchetes)?\n"
            "4. **Voz Narrativa em 1ª Pessoa:** os bullets de experiência e projetos usam verbos em 1ª pessoa ('Atuo...', 'Desenvolvi...', 'Implementei...') indicando protagonismo e autoria, e NÃO em 3ª pessoa impessoal ('Atua', 'Desenvolveu')?\n\n"
            "Avalie a qualidade ATS:\n"
            "- Atribua um ats_score de 0 a 100 baseado na fidelidade, clareza e densidade das keywords comprovadas (nunca atribua notas altas se o candidato tiver lacunas técnicas não comprovadas na vaga).\n"
            "- Liste em applied_changes de 3 a 5 adequações realizadas em relação ao currículo base.\n"
            "- Forneça em interview_tips de 2 a 3 orientações para entrevista técnica sobre como defender os requisitos da vaga e destacar os projetos reais.\n"
            "- Classifique severity em 'approved' (aprovado), 'minor' (problema pontual em 1 seção específica) ou 'major' (alucinação grave/reescrita total).\n"
            "- Se severity for 'minor', indique em target_section exatamente qual seção deve ser corrigida (ex.: 'HABILIDADES TÉCNICAS', 'PROJETOS EM DESTAQUE', 'RESUMO PROFISSIONAL').\n\n"
            "--- VAGA ALVO ---\n{job_context}\n\n"
            "--- TECNOLOGIAS COMPROVADAS ---\n{verified}\n\n"
            "--- PENDÊNCIAS TÉCNICAS (o candidato NÃO possui; não podem aparecer como experiência) ---\n{gaps}\n\n"
            "--- CURRÍCULO BASE ---\n{base_resume}\n\n"
            "--- READMEs FORNECIDOS ---\n{portfolio_context}\n\n"
            "--- CURRÍCULO GERADO (Para revisão) ---\n{generated}\n\n"
            "Retorne a análise estruturada."
        )
        result = llm.invoke_tracked(prompt | structured_llm, {
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
