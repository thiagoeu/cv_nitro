"""Validador determinístico Tier 1 (0 tokens de LLM), cálculo de score ATS e roteiro de entrevista."""
import re
from typing import Optional
from src.agents.shared.sections import section_of, unfilled_placeholders
from src.core import competency_matcher as competency_matcher_core


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

