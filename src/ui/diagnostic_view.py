import streamlit as st
from typing import Dict, Any

def render_ats_diagnostic_panel(diagnostic: Dict[str, Any]):
    """
    Renderiza o painel visual com o diagnóstico de conformidade ATS,
    score de aderência, palavras-chave alinhadas e parecer do auditor.
    """
    if not diagnostic:
        st.info("Nenhum dado de diagnóstico detalhado registrado para esta candidatura.")
        return

    # Falhas não fatais da execução (GitHub, revisor, carta) gravadas junto da candidatura
    for warning in diagnostic.get("run_warnings") or []:
        st.warning(warning, icon=":material/warning:")

    ats_score = int(diagnostic.get("ats_score", 80))
    matched_keywords = diagnostic.get("matched_keywords", [])
    missing_keywords = diagnostic.get("missing_keywords", [])
    curated_repos = diagnostic.get("curated_repos", [])
    interview_tips = diagnostic.get("interview_tips", [])
    agent_trace = diagnostic.get("agent_trace", [])
    stop_reason = diagnostic.get("stop_reason")
    applied_changes = diagnostic.get("applied_changes", [])
    reviewer_summary = diagnostic.get("reviewer_summary", "")

    # Linha com Métricas Principais
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.metric(
            label="Compatibilidade ATS",
            value=f"{ats_score}%",
            help="Score baseado em formatação, palavras-chave e adequação estrutural.",
            border=True
        )
        label = "Excelente" if ats_score >= 85 else "Bom" if ats_score >= 70 else "Precisa de ajustes"
        st.progress(min(max(ats_score, 0), 100) / 100, text=label)
    with col2:
        st.metric(
            label="Keywords alinhadas",
            value=f"{len(matched_keywords)} termos",
            help="Termos técnicos e soft skills identificados na vaga e integrados ao currículo.",
            border=True
        )
    with col3:
        if reviewer_summary:
            st.info(f"**Parecer do revisor:** {reviewer_summary}", icon=":material/rate_review:")

    # Colunas de Detalhes: Alterações Realizadas vs Palavras-Chave Alinhadas
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/build: Ajustes realizados")
            changes = applied_changes or [
                "Padronização executiva em formato Markdown ATS",
                "Tabela de competências e bullets com verbos de ação"
            ]
            st.markdown("\n".join(f"- :green[:material/check:] {c}" for c in changes))

    with col_right:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/key: Palavras-chave e tecnologias")
            if matched_keywords:
                st.markdown(" ".join(f":blue-badge[{k}]" for k in matched_keywords))
            else:
                st.caption("Nenhuma palavra-chave específica foi destacada.")

    # Seção de Lacunas Identificadas (Gaps) e Curadoria GitHub
    col_gap, col_repo = st.columns([1, 1])
    with col_gap:
        with st.container(border=True):
            st.markdown("#### :material/rule: Lacunas identificadas na vaga (*Gaps*)")
            st.caption("Requisitos da vaga não evidenciados no currículo base ou portfólio (mantidos em aberto para evitar alucinações).")
            if missing_keywords:
                st.markdown(" ".join(f":orange-badge[{m}]" for m in missing_keywords))
            else:
                st.success("Nenhuma lacuna técnica crítica identificada em relação aos requisitos detectados.", icon=":material/verified:")

    with col_repo:
        with st.container(border=True):
            st.markdown("#### :material/folder_special: Portfólio curado do GitHub")
            st.caption("Projetos autorais com maior pontuação algorítmica de aderência à stack da vaga.")
            if curated_repos:
                for cr in curated_repos:
                    score = cr.get("relevance_score", 0.0)
                    lang = cr.get("language") or "Multi-stack"
                    url = cr.get("url")
                    name = cr.get("name", "Repositório")
                    link_md = f"[{name}]({url})" if url else name
                    st.markdown(f"- :material/commit: **{link_md}** (`{lang}`) — :blue-badge[Score: {score:.1f}]")
            else:
                st.caption("Nenhum repositório específico do GitHub foi cruzado para esta vaga.")

    # Seção de Preparação para Entrevista Técnica
    if interview_tips:
        with st.container(border=True):
            st.markdown("#### :material/psychology: Guia estratégico para entrevista técnica")
            st.caption("Recomendações baseadas nas lacunas abertas e nos projetos reais para defender sua candidatura perante o recrutador:")
            for tip in interview_tips:
                st.markdown(f"- :material/arrow_forward: {tip}")

    # Seção de Observabilidade e Deliberação dos Agentes (Agent Trace)
    if agent_trace:
        with st.expander(":material/route: Linha do tempo de deliberação dos agentes (*Agent Execution Trace*)", expanded=False):
            st.caption("Rastro estruturado da comunicação, decisões de roteamento e snapshots executados pelo grafo:")
            status_icons = {
                "success": ":green[:material/check_circle:]",
                "info": ":blue[:material/info:]",
                "warning": ":orange[:material/warning:]",
                "error": ":red[:material/error:]"
            }
            for idx, trace in enumerate(agent_trace):
                icon = status_icons.get(trace.get("status", "info"), ":material/arrow_right:")
                agent = trace.get("agent", "Agente")
                step = trace.get("step", f"Etapa {idx+1}")
                detail = trace.get("detail", "")
                st.markdown(f"**{idx+1}. {icon} `{agent}` — {step}**")
                if detail:
                    st.caption(detail)
