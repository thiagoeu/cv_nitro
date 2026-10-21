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

    st.markdown("#### 🎯 Raio-X & Diagnóstico de Otimização ATS")
    st.caption("Avaliação de conformidade com sistemas de triagem automatizada (ATS) e parecer dos agentes de IA.")

    # Linha com Métricas Principais
    col1, col2, col3 = st.columns([1.2, 1.2, 2.5])
    with col1:
        score_color = "🟢" if ats_score >= 85 else "🟡" if ats_score >= 70 else "🔴"
        st.metric(
            label="Compatibilidade ATS",
            value=f"{ats_score}% {score_color}",
            help="Score baseado em formatação, palavras-chave e adequação estrutural."
        )
    with col2:
        st.metric(
            label="Keywords Alinhadas",
            value=f"{len(matched_keywords)} termos",
            help="Termos técnicos e soft skills identificados na vaga e integrados ao currículo."
        )
    with col3:
        if reviewer_summary:
            st.info(f"**Parecer do Revisor:** {reviewer_summary}")

    st.markdown("---")

    # Colunas de Detalhes: Alterações Realizadas vs Palavras-Chave
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("##### 🛠️ Ajustes e Otimizações Realizadas")
        if applied_changes:
            for change in applied_changes:
                st.markdown(f"- ✅ **{change}**")
        else:
            st.write("- ✅ Padronização executiva em formato Markdown ATS")
            st.write("- ✅ Tabela de competências e bullets com verbos de ação")

    with col_right:
        st.markdown("##### 🔑 Palavras-Chave & Tecnologias")
        if matched_keywords:
            badge_html = " ".join([
                f'<span style="display:inline-block; background-color:#2e3846; color:#a5d8ff; '
                f'border-radius:6px; padding:3px 8px; margin:2px; font-size:12px; font-weight:600;">'
                f'{k}</span>'
                for k in matched_keywords
            ])
            st.markdown(badge_html, unsafe_allow_html=True)
        else:
            st.caption("Nenhuma palavra-chave específica foi destacada.")
