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

    ats_score = int(diagnostic.get("ats_score", 80))
    matched_keywords = diagnostic.get("matched_keywords", [])
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

    # Colunas de Detalhes: Alterações Realizadas vs Palavras-Chave
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
