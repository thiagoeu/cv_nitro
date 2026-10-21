import streamlit as st
import pandas as pd
from collections import Counter
from src.core import history_manager
from src.ui.navbar import set_page

def render_dashboard_view(resumes: list):
    """
    Renderiza o painel executivo de métricas e gráficos analíticos.
    Protege o acesso a dados exigindo usuário autenticado.
    """
    session = st.session_state.get("user_session", {})
    is_guest = session.get("is_guest", True)

    st.markdown("### 📊 Painel Geral de Candidaturas")
    st.caption("Visão executiva do seu funil e métricas de mercado (ordenado por data mais recente).")

    # Controle de Acesso: Requer Login para Visualizar Dados Privados
    if is_guest:
        st.warning("🔒 **Acesso Exclusivo para Usuários Conectados**\n\nO Dashboard consolida métricas privadas, funil de candidaturas e comparativos ATS das suas vagas. Faça login ou crie sua conta para desbloquear seu painel analítico.")
        col_login, col_signup = st.columns(2)
        with col_login:
            if st.button("🔑 Acessar Minha Conta", type="primary", key="dash_btn_login_auth", use_container_width=True):
                set_page("login")
                st.rerun()
        with col_signup:
            if st.button("✨ Criar Conta Gratuita", key="dash_btn_signup_auth", use_container_width=True):
                set_page("signup")
                st.rerun()
        return
    
    if not resumes:
        st.info("Nenhuma candidatura registrada ainda. Clique no botão abaixo para gerar seu primeiro currículo otimizado!")
        if st.button("🚀 Iniciar Nova Otimização", type="primary", key="dash_btn_empty_start"):
            set_page("wizard")
            st.rerun()
        return

    # Cálculos das Métricas
    total_apps = len(resumes)
    en_apps = sum(1 for r in resumes if str(r.get("language", "")).lower() == "en")
    pt_apps = sum(1 for r in resumes if str(r.get("language", "")).lower() != "en")
    
    all_techs = []
    scores = []
    for r in resumes:
        all_techs.extend(r.get("technologies", []))
        diag = r.get("diagnostic", {})
        if diag and "ats_score" in diag:
            scores.append(diag["ats_score"])

    tech_counter = Counter([t.strip().capitalize() for t in all_techs if t.strip()])
    avg_score = int(sum(scores) / len(scores)) if scores else 85
    
    # Cards de Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Aplicações", total_apps)
    m2.metric("Score ATS Médio", f"{avg_score}%")
    m3.metric("Vagas em Inglês (EN)", en_apps)
    m4.metric("Tecnologias Mapeadas", len(tech_counter))
    
    st.markdown("---")
    
    # Gráficos de Tendência
    col_chart1, col_chart2 = st.columns([2, 1])
    with col_chart1:
        st.markdown("##### 🚀 Tecnologias Mais Demandadas nas Vagas")
        if tech_counter:
            top_techs = dict(tech_counter.most_common(10))
            df_techs = pd.DataFrame(list(top_techs.items()), columns=["Tecnologia", "Ocorrências"]).set_index("Tecnologia")
            st.bar_chart(df_techs)
        else:
            st.info("As tecnologias serão exibidas conforme novas vagas forem analisadas.")
            
    with col_chart2:
        st.markdown("##### 🌐 Idiomas das Vagas")
        lang_data = pd.DataFrame({
            "Idioma": ["Inglês", "Português/Outros"],
            "Candidaturas": [en_apps, pt_apps]
        }).set_index("Idioma")
        st.bar_chart(lang_data)

    st.markdown("---")
    st.markdown("##### 📋 Candidaturas Mais Recentes")
    
    cols_buttons = st.columns(min(len(resumes), 4))
    for i, r in enumerate(resumes[:4]):
        col_btn = cols_buttons[i % 4]
        job_t = r.get("job_title", "Vaga")
        date_t = history_manager.format_display_date(r.get("date", ""))
        btn_caption = f"📄 {job_t[:16]}...\n({date_t})"
        if col_btn.button(btn_caption, key=f"dash_btn_{i}", use_container_width=True):
            st.session_state.viewing_history = r["filepath"]
            set_page("applications", clear_transient=False)
            st.rerun()
