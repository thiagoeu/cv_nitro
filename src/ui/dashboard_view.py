import streamlit as st
import pandas as pd
from collections import Counter
from src.ui.navbar import set_page
from src.ui.components import page_header, login_gate, application_card

def render_dashboard_view(resumes: list):
    """
    Renderiza o painel executivo de métricas e gráficos analíticos.
    Protege o acesso a dados exigindo usuário autenticado.
    """
    session = st.session_state.get("user_session", {})
    is_guest = session.get("is_guest", True)

    actions = page_header("Dashboard", "Visão geral do seu funil de candidaturas e do que o mercado está pedindo.")

    # Controle de Acesso: Requer Login para Visualizar Dados Privados
    if is_guest:
        login_gate(
            "Acesso Exclusivo para Usuários Conectados",
            "O Dashboard consolida métricas privadas, funil de candidaturas e comparativos ATS das suas vagas. "
            "Faça login ou crie sua conta para desbloquear seu painel analítico.",
            key="dash"
        )
        return

    with actions:
        if st.button("Nova otimização", type="primary", icon=":material/add:", key="dash_btn_new", width="stretch"):
            set_page("wizard")
            st.rerun()

    if not resumes:
        st.info("Nenhuma candidatura registrada ainda. Use **Nova otimização** para gerar seu primeiro currículo otimizado.", icon=":material/info:")
        return

    # Cálculos das Métricas
    total_apps = len(resumes)
    en_apps = sum(1 for r in resumes if str(r.get("language", "")).lower() == "en")

    all_techs = []
    scores = []
    for r in resumes:
        all_techs.extend(r.get("technologies", []))
        diag = r.get("diagnostic", {})
        if diag and "ats_score" in diag:
            scores.append(diag["ats_score"])

    tech_counter = Counter([t.strip().capitalize() for t in all_techs if t.strip()])

    # Cards de Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Candidaturas", total_apps, border=True)
    m2.metric("Score ATS médio", f"{int(sum(scores) / len(scores))}%" if scores else "—", border=True)
    m3.metric("Vagas em inglês", f"{en_apps} de {total_apps}", border=True)
    m4.metric("Tecnologias mapeadas", len(tech_counter), border=True)

    col_chart, col_recent = st.columns([3, 2], gap="medium")
    with col_chart:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/bar_chart: Tecnologias mais pedidas")
            if tech_counter:
                df_techs = pd.DataFrame(tech_counter.most_common(10), columns=["Tecnologia", "Vagas"])
                st.bar_chart(df_techs, x="Tecnologia", y="Vagas", horizontal=True, sort="-Vagas", color="#6366f1", x_label="", y_label="")
            else:
                st.caption("As tecnologias aparecem aqui conforme novas vagas forem analisadas.")

    with col_recent:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/schedule: Candidaturas recentes")
            for i, r in enumerate(resumes[:5]):
                application_card(r, key=f"dash_btn_{i}")
