import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

from src.core import history_manager, config, auth_manager, profile_manager, db_migrator
from src.core.document_parser import extract_text_from_file
from src.core.resume_formatter import format_resume_to_html
from src.agents.graph import build_graph
from src.agents.state import GraphState
from src.ui.diagnostic_view import render_ats_diagnostic_panel

# Configuração da página
st.set_page_config(
    page_title="GitMatch - CV Nitro Optimizer & Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Compilação do grafo LangGraph
graph = build_graph()

# Inicialização da Sessão do Usuário
if "user_session" not in st.session_state:
    st.session_state.user_session = auth_manager.create_guest_session()

# Cache de alta performance para resposta instantânea ao clicar no Acesso Rápido
@st.cache_data(ttl=30, show_spinner=False)
def get_cached_resumes(user_id: str = "guest_local"):
    """Recupera lista de candidaturas com cache curto para garantir carregamento instantâneo."""
    return history_manager.list_resumes(user_id=user_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_application(filepath: str):
    """Carrega dados da aplicação com cache em memória para visualização sem latência de rede."""
    return history_manager.load_application(filepath)

def clear_history_cache():
    """Invalida o cache de leitura após salvar, atualizar ou excluir candidaturas."""
    get_cached_resumes.clear()
    get_cached_application.clear()

def show_errors(errors: list):
    for err in errors or []:
        st.warning(f"⚠️ {err}")

def render_auth_header():
    """Renderiza o controle de autenticação do usuário na barra lateral."""
    session = st.session_state.get("user_session", auth_manager.create_guest_session())
    is_guest = session.get("is_guest", True)

    if is_guest:
        st.sidebar.caption("👤 **Status:** Convidado (Modo Local)")
        with st.sidebar.popover("🔑 Entrar / Cadastrar", use_container_width=True):
            tab_login, tab_signup = st.tabs(["Entrar", "Criar Conta"])
            with tab_login:
                st.markdown("##### 🔐 Acessar sua conta")
                l_email = st.text_input("E-mail", key="auth_login_email")
                l_pass = st.text_input("Senha", type="password", key="auth_login_pass")
                if st.button("Fazer Login", type="primary", use_container_width=True, key="btn_do_login"):
                    res = auth_manager.sign_in_with_password(l_email, l_pass)
                    if res["success"]:
                        st.session_state.user_session = res["user"]
                        clear_history_cache()
                        st.toast(f"Bem-vindo(a), {res['user']['display_name']}!")
                        st.rerun()
                    else:
                        st.error(res["error"])
            with tab_signup:
                st.markdown("##### 📝 Nova conta")
                s_name = st.text_input("Seu Nome", key="auth_signup_name")
                s_email = st.text_input("E-mail", key="auth_signup_email")
                s_pass = st.text_input("Senha (mín. 6 chars)", type="password", key="auth_signup_pass")
                if st.button("Cadastrar", type="primary", use_container_width=True, key="btn_do_signup"):
                    res = auth_manager.sign_up(s_email, s_pass, full_name=s_name)
                    if res["success"]:
                        st.session_state.user_session = res["user"]
                        clear_history_cache()
                        st.success(res.get("message", "Conta criada com sucesso!"))
                        st.rerun()
                    else:
                        st.error(res["error"])
    else:
        st.sidebar.markdown(f"🟢 **Olá, {session.get('display_name', 'Candidato')}**")
        st.sidebar.caption(f"Email: `{session.get('email', '')}`")
        if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True, key="btn_logout"):
            auth_manager.sign_out()
            st.session_state.user_session = auth_manager.create_guest_session()
            clear_history_cache()
            st.toast("Sessão encerrada.")
            st.rerun()
            
    st.sidebar.markdown("---")

def render_sidebar():
    st.sidebar.title("🎯 GitMatch - CV Nitro")
    st.sidebar.caption("Otimizador Multi-Agente & Diagnóstico ATS")
    st.sidebar.markdown("---")
    
    # Controle de Autenticação / Perfil
    render_auth_header()

    # Navegação Principal
    page = st.sidebar.radio(
        "Navegação",
        [
            "📊 Dashboard Executivo",
            "🚀 Nova Otimização (Wizard)",
            "📚 Central de Candidaturas",
            "⚙️ Configurações & Status"
        ],
        index=st.session_state.get("nav_index", 0)
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Acesso Rápido")
    st.sidebar.caption("🕒 Mais recentes primeiro:")
    
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    resumes = get_cached_resumes(current_uid)
    if not resumes:
        st.sidebar.caption("Nenhuma candidatura salva ainda.")
    else:
        for idx, resume in enumerate(resumes[:8]):
            date_display = history_manager.format_display_date(resume.get('date', ''))
            job_title = resume.get('job_title', 'Vaga Desconhecida')
            lang = (resume.get('language') or 'pt').upper()
            
            btn_label = f"[{lang}] {job_title[:15]}... ({date_display})"
            if st.sidebar.button(btn_label, key=f"sidebar_hist_{idx}", width="stretch"):
                st.session_state.viewing_history = resume['filepath']
                st.rerun()
                
    return page

def render_application_view(filepath: str):
    app_data = get_cached_application(filepath)
    metadata = app_data.get("metadata", {})
    job_title = metadata.get("job_title", "Vaga")
    job_url = metadata.get("job_url", "")
    lang = (metadata.get("language") or "pt").upper()
    date_str = history_manager.format_display_date(metadata.get("date", ""))
    diagnostic = metadata.get("diagnostic", {})
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    
    col_back, col_rerun, col_delete = st.columns([1.5, 2.5, 2.0])
    with col_back:
        if st.button("← Voltar à Lista", width="stretch"):
            if "viewing_history" in st.session_state:
                del st.session_state.viewing_history
            st.rerun()
    with col_rerun:
        is_rerun_open = st.session_state.get(f"show_rerun_{filepath}", False)
        btn_label = "✖️ Fechar Re-otimização" if is_rerun_open else "🔄 Re-otimizar com IA"
        if st.button(btn_label, type="primary" if not is_rerun_open else "secondary", width="stretch"):
            st.session_state[f"show_rerun_{filepath}"] = not is_rerun_open
            st.rerun()
    with col_delete:
        with st.popover("🗑️ Excluir", use_container_width=True):
            st.markdown("⚠️ **Excluir esta candidatura?**")
            st.caption("Esta ação remove o currículo e diagnóstico permanentemente.")
            if st.button("Sim, Excluir Definitivamente", type="primary", key=f"btn_confirm_del_{filepath}", width="stretch"):
                history_manager.delete_application(filepath)
                clear_history_cache()
                if "viewing_history" in st.session_state:
                    del st.session_state.viewing_history
                st.toast("Candidatura excluída com sucesso!")
                st.rerun()
            
    # Painel interativo de Re-otimização
    if st.session_state.get(f"show_rerun_{filepath}", False):
        with st.expander("⚡ Re-otimizar Candidatura com Opções de IA", expanded=True):
            st.info("Re-execute o fluxo multi-agente ajustando parâmetros ou o currículo base.")
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                r_title = st.text_input("Título da Vaga *", value=job_title, key=f"r_title_{filepath}")
            with col_r2:
                r_url = st.text_input("Link da Vaga (opcional)", value=job_url, key=f"r_url_{filepath}")
                
            r_github = st.text_input("Usuário do GitHub (opcional)", value=metadata.get("github_username", ""), key=f"r_gh_{filepath}")
            
            saved_desc = metadata.get("job_description", "")
            r_desc = st.text_area(
                "Descrição Completa da Vaga *",
                value=saved_desc,
                height=160,
                key=f"r_desc_{filepath}"
            )
            
            default_base = metadata.get("base_resume") or app_data.get("resume_md", "")
            r_base = st.text_area(
                "Currículo Base do Candidato *",
                value=default_base,
                height=180,
                key=f"r_base_{filepath}"
            )
            
            col_ropt1, col_ropt2 = st.columns(2)
            with col_ropt1:
                r_cover = st.checkbox("✉️ Gerar Carta de Apresentação", value=metadata.get("has_cover_letter", True), key=f"r_c_{filepath}")
            with col_ropt2:
                r_strict = st.checkbox("🔍 Auditoria Rígida de Qualidade", value=False, key=f"r_s_{filepath}")
            
            if st.button("🚀 Iniciar Re-otimização Agora", type="primary", width="stretch", key=f"r_submit_{filepath}"):
                if not r_title or not r_desc or not r_base:
                    st.error("Preencha o título da vaga, descrição e currículo base!")
                else:
                    initial_state = GraphState(
                        job_description=r_desc,
                        base_resume_md=r_base,
                        github_username=r_github,
                        job_url=r_url,
                        job_keywords=[],
                        job_technologies=[],
                        job_language="pt",
                        github_repos=[],
                        github_readmes={},
                        generated_resume_md=None,
                        generated_cover_letter_md=None,
                        reviewer_feedback=None,
                        reviewer_approved=False,
                        review_attempts=0,
                        generate_cover_letter=r_cover,
                        strict_review=r_strict
                    )
                    with st.status("Re-executando fluxo multi-agente...", expanded=True) as status:
                        st.write("🔍 Analisando vaga e aplicando otimizações...")
                        try:
                            final_state = graph.invoke(initial_state)
                            status.update(label="Re-otimização concluída com sucesso!", state="complete", expanded=False)
                            
                            new_resume_md = final_state.get("generated_resume_md", "")
                            new_cover_md = final_state.get("generated_cover_letter_md", "")
                            new_lang = final_state.get("job_language", "pt")
                            new_techs = final_state.get("job_technologies", [])
                            new_diag = final_state.get("diagnostic", {})
                            
                            history_manager.save_resume(
                                job_title=r_title,
                                content=new_resume_md,
                                job_url=r_url,
                                cover_letter=new_cover_md,
                                language=new_lang,
                                technologies=new_techs,
                                job_description=r_desc,
                                base_resume=r_base,
                                github_username=r_github,
                                filepath=filepath,
                                diagnostic=new_diag,
                                user_id=current_uid
                            )
                            clear_history_cache()
                            st.session_state[f"show_rerun_{filepath}"] = False
                            st.session_state[f"run_errors_{filepath}"] = final_state.get("errors", [])
                            st.rerun()
                        except Exception as e:
                            status.update(label="Falha na re-otimização", state="error", expanded=True)
                            st.error(f"Erro durante a execução: {e}")
            
    if f"run_errors_{filepath}" in st.session_state:
        st.success("Currículo otimizado e salvo com sucesso!")
        show_errors(st.session_state.pop(f"run_errors_{filepath}"))

    st.subheader(f"💼 {job_title}")

    # Metadados em badges
    meta_cols = st.columns(4)
    with meta_cols[0]:
        st.markdown(f"**Data da Otimização:** `{date_str}`")
    with meta_cols[1]:
        st.markdown(f"**Idioma Identificado:** `{lang}`")
    with meta_cols[2]:
        if job_url:
            st.markdown(f"**Link da Vaga:** [🔗 Acessar Link Externo]({job_url})")
        else:
            st.markdown("**Link da Vaga:** *(Não informado)*")
    with meta_cols[3]:
        techs = metadata.get("technologies", [])
        if techs:
            st.markdown(f"**Tecnologias:** {', '.join(techs[:3])}")
            
    st.markdown("---")
    
    # Abas com Diagnóstico, Currículo A4, Markdown e Carta
    tab_diag, tab_a4, tab_cv, tab_letter = st.tabs([
        "🎯 Diagnóstico ATS & Feedback",
        "📑 Folha Formatada (A4 / Impressão)",
        "📄 Markdown Puro",
        "✉️ Carta de Apresentação (Cover Letter)"
    ])
    
    resume_md = app_data.get("resume_md", "")
    cover_letter_md = app_data.get("cover_letter_md", "")
    formatted_html = format_resume_to_html(resume_md, job_title)
    
    with tab_diag:
        render_ats_diagnostic_panel(diagnostic)

    with tab_a4:
        col_down_html, _ = st.columns([1, 2])
        with col_down_html:
            st.download_button(
                label="🖨️ Baixar HTML Imprimível (Salvar como PDF)",
                data=formatted_html,
                file_name=f"Curriculo_{job_title.replace(' ', '_')}.html",
                mime="text/html",
                width="stretch"
            )
        st.iframe(formatted_html, height=1000)
        
    with tab_cv:
        st.download_button(
            label="📥 Baixar Currículo (.md)",
            data=resume_md,
            file_name=f"Curriculo_{job_title.replace(' ', '_')}.md",
            mime="text/markdown"
        )
        st.markdown(resume_md if resume_md else "_Nenhum conteúdo de currículo encontrado._")
        
    with tab_letter:
        if cover_letter_md:
            st.download_button(
                label="📥 Baixar Cover Letter (.md)",
                data=cover_letter_md,
                file_name=f"CoverLetter_{job_title.replace(' ', '_')}.md",
                mime="text/markdown"
            )
            st.markdown(cover_letter_md)
        else:
            st.info("Esta aplicação não possui uma Cover Letter gerada.")

def render_dashboard(resumes: list):
    st.markdown("### 📊 Painel Geral de Candidaturas")
    st.caption("Visão executiva do seu funil e métricas de mercado (ordenado por data mais recente).")
    
    if not resumes:
        st.info("Nenhuma candidatura registrada ainda. Vá para a aba **🚀 Nova Otimização** para gerar seu primeiro currículo!")
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
    
    # Gráficos
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
        btn_caption = f"Abrir: {job_t[:16]}...\n({date_t})"
        if col_btn.button(btn_caption, key=f"dash_btn_{i}", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            st.rerun()

def render_new_optimization():
    st.markdown("### 🚀 Assistente de Otimização de Currículo")
    st.caption("Preencha as informações abaixo passo a passo para a IA analisar a vaga e estruturar o melhor currículo ATS.")
    
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    current_email = st.session_state.user_session.get("email", "")
    user_prof = profile_manager.get_user_profile(current_uid, current_email)
    
    # ETAPA 1
    st.markdown("#### 1. Currículo Base do Candidato")
    uploaded_file = st.file_uploader(
        "Faça upload do seu currículo atual (PDF, DOCX, Markdown ou TXT):",
        type=["pdf", "docx", "md", "txt"],
        help="Extraímos automaticamente o texto mantendo o histórico de suas experiências."
    )
    
    extracted_text = ""
    if uploaded_file is not None:
        try:
            extracted_text = extract_text_from_file(uploaded_file)
            st.success(f"Texto extraído com sucesso de **{uploaded_file.name}** ({len(extracted_text)} caracteres).")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            
    # Pré-preenchimento inteligente a partir do perfil
    default_base_text = extracted_text or user_prof.get("base_resume", "")
    if user_prof.get("base_resume") and not extracted_text:
        st.info("💡 **Currículo base carregado do seu perfil salvo!** Você pode editar abaixo ou manter como está.")
        
    base_resume = st.text_area(
        "Texto do Currículo Base (edite ou cole diretamente aqui):",
        value=default_base_text,
        height=200,
        placeholder="Cole seu currículo aqui ou faça o upload do arquivo acima...",
        key="wizard_base_resume"
    )
    
    st.markdown("---")
    # ETAPA 2
    st.markdown("#### 2. Informações da Vaga Alvo")
    col_vaga1, col_vaga2 = st.columns([2, 1])
    with col_vaga1:
        job_title = st.text_input("Título da Vaga *", placeholder="Ex: Senior Python Engineer / Especialista em Dados", key="wizard_job_title")
    with col_vaga2:
        job_url = st.text_input("Link da Vaga (URL opcional)", placeholder="Ex: https://linkedin.com/jobs/view/...", key="wizard_job_url")
        
    default_github = user_prof.get("github_username", "")
    github_user = st.text_input(
        "Usuário do GitHub (opcional para cruzar projetos reais)",
        value=default_github,
        placeholder="Ex: octocat",
        help="Preenchido automaticamente a partir do seu perfil para economizar consultas e tokens.",
        key="wizard_github_user"
    )
    job_desc = st.text_area("Descrição Completa da Vaga *", height=180, placeholder="Cole aqui a descrição dos requisitos e responsabilidades da vaga...", key="wizard_job_desc")
    
    st.markdown("---")
    # ETAPA 3
    st.markdown("#### 3. Preferências de IA & Economia de Tokens")
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        gen_cover = st.checkbox(
            "✉️ Gerar Carta de Apresentação (Cover Letter)",
            value=True,
            help="Desmarque se você precisa apenas do currículo para economizar tokens."
        )
    with col_opt2:
        strict_rev = st.checkbox(
            "🔍 Auditoria Rígida de Qualidade (Quality Reviewer)",
            value=False,
            help="Ative para auditoria com loop de refinamento; desative para modo econômico e resposta ultra-rápida."
        )

    st.markdown("---")
    submit = st.button("Gerar Currículo Otimizado & Diagnóstico ATS 🚀", type="primary", width="stretch", key="wizard_submit_btn")
    
    if submit:
        if not job_title or not job_desc or not base_resume:
            st.error("Por favor, preencha os campos obrigatórios: Título da vaga, Descrição da vaga e Currículo base!")
            return
            
        initial_state = GraphState(
            job_description=job_desc,
            base_resume_md=base_resume,
            github_username=github_user,
            job_url=job_url,
            job_keywords=[],
            job_technologies=[],
            job_language="pt",
            github_repos=[],
            github_readmes={},
            generated_resume_md=None,
            generated_cover_letter_md=None,
            reviewer_feedback=None,
            reviewer_approved=False,
            review_attempts=0,
            generate_cover_letter=gen_cover,
            strict_review=strict_rev
        )
        
        with st.status("Executando fluxo multi-agente...", expanded=True) as status:
            st.write("🔍 Analisando a vaga e identificando palavras-chave e idioma...")
            try:
                final_state = graph.invoke(initial_state)
            except Exception as e:
                status.update(label="Falha na execução", state="error", expanded=True)
                st.error(f"Erro durante a execução do grafo: {e}")
                return
            status.update(label="Otimização concluída com sucesso!", state="complete", expanded=False)

        saved_path = history_manager.save_resume(
            job_title=job_title,
            content=final_state.get("generated_resume_md", ""),
            job_url=job_url,
            cover_letter=final_state.get("generated_cover_letter_md", ""),
            language=final_state.get("job_language", "pt"),
            technologies=final_state.get("job_technologies", []),
            job_description=job_desc,
            base_resume=base_resume,
            github_username=github_user,
            diagnostic=final_state.get("diagnostic", {}),
            user_id=current_uid
        )
        clear_history_cache()
        st.session_state[f"run_errors_{saved_path}"] = final_state.get("errors", [])
        st.session_state.viewing_history = saved_path
        st.rerun()

def render_applications_list(resumes: list):
    st.markdown("### 📚 Central de Candidaturas")
    st.caption("Gerenciador completo de todas as suas candidaturas (ordenadas da mais recente à mais antiga).")
    
    if not resumes:
        st.info("Nenhuma candidatura encontrada no histórico.")
        return
        
    search_query = st.text_input("🔍 Filtrar candidaturas por vaga ou tecnologia:", placeholder="Ex: Python, React, Senior...")
    
    filtered_resumes = resumes
    if search_query:
        q = search_query.lower()
        filtered_resumes = [
            r for r in resumes
            if q in r.get("job_title", "").lower() or any(q in t.lower() for t in r.get("technologies", []))
        ]
        
    st.write(f"Exibindo **{len(filtered_resumes)}** de **{len(resumes)}** candidaturas registradas.")
    
    table_rows = []
    for r in filtered_resumes:
        date_fmt = history_manager.format_display_date(r.get("date", ""))
        raw_url = r.get("job_url", "")
        valid_url = raw_url if (raw_url and (raw_url.startswith("http://") or raw_url.startswith("https://"))) else None
        diag = r.get("diagnostic", {})
        score = f"{diag.get('ats_score', 85)}%" if diag else "-"
        table_rows.append({
            "Vaga": r.get("job_title", "Vaga"),
            "Idioma": (r.get("language") or "pt").upper(),
            "Score ATS": score,
            "Data do Ajuste": date_fmt,
            "Link da Vaga": valid_url,
            "Cover Letter": "Sim" if r.get("has_cover_letter") else "Não",
            "_filepath": r.get("filepath")
        })
        
    df_table = pd.DataFrame(table_rows)
    st.dataframe(
        df_table[["Vaga", "Idioma", "Score ATS", "Data do Ajuste", "Link da Vaga", "Cover Letter"]],
        column_config={
            "Link da Vaga": st.column_config.LinkColumn(
                "Link da Vaga",
                help="Acesse o anúncio externo da vaga",
                display_text="Acessar Vaga 🔗"
            )
        },
        width="stretch",
        hide_index=True
    )
    
    st.markdown("##### 📄 Abrir Candidatura para Visualização e Impressão:")
    cols = st.columns(min(len(filtered_resumes), 3))
    for idx, r in enumerate(filtered_resumes[:6]):
        col = cols[idx % 3]
        job_label = r.get('job_title', 'Vaga')[:20]
        date_label = history_manager.format_display_date(r.get('date', ''))
        if col.button(f"{job_label}\n({date_label})", key=f"hist_card_{idx}", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            st.rerun()

def render_settings():
    st.markdown("### ⚙️ Configurações & Status do Sistema")
    st.caption("Verifique o status das conexões com o banco de dados na nuvem, seu perfil do candidato e provedores de Inteligência Artificial.")
    
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    current_email = st.session_state.user_session.get("email", "")

    # 1. Perfil do Candidato (Currículo Base & Cache GitHub)
    st.markdown("#### 👤 Meu Perfil de Candidato (Currículo Base & Projetos)")
    st.caption("Salve seus dados aqui para que o assistente os reutilize automaticamente, eliminando digitação e economizando tokens.")
    
    prof = profile_manager.get_user_profile(current_uid, current_email)
    
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        p_name = st.text_input("Nome Completo do Candidato", value=prof.get("full_name", ""), key="settings_p_name")
    with col_p2:
        p_github = st.text_input("Usuário do GitHub", value=prof.get("github_username", ""), key="settings_p_github")

    p_resume = st.text_area(
        "Currículo Base Padrão (Markdown ou texto puro)",
        value=prof.get("base_resume", ""),
        height=200,
        help="Este currículo será inserido automaticamente em qualquer nova otimização.",
        key="settings_p_resume"
    )

    col_save_p, col_gh_fetch = st.columns(2)
    with col_save_p:
        if st.button("💾 Salvar Perfil do Candidato", type="primary", width="stretch", key="btn_save_profile"):
            updated_prof = {
                "email": current_email,
                "full_name": p_name,
                "github_username": p_github,
                "base_resume": p_resume,
                "cached_repos": prof.get("cached_repos", []),
                "skills": prof.get("skills", [])
            }
            profile_manager.save_user_profile(current_uid, updated_prof)
            st.toast("Perfil salvo com sucesso!")
            st.success("Currículo base e dados de perfil foram atualizados.")
            
    with col_gh_fetch:
        if st.button("🔄 Atualizar Cache do GitHub", width="stretch", key="btn_sync_gh_cache", help="Busca seus repositórios no GitHub para alimentar o cache de economia de tokens"):
            if not p_github:
                st.warning("Preencha o usuário do GitHub acima para buscar seus projetos.")
            else:
                with st.spinner(f"Buscando projetos públicos de @{p_github}..."):
                    from src.agents.nodes import github_researcher
                    gh_state = {"github_username": p_github, "job_technologies": []}
                    gh_res = github_researcher(gh_state)
                    repos = gh_res.get("github_repos", [])
                    profile_manager.update_cached_github_repos(current_uid, repos)
                    st.toast(f"{len(repos)} projeto(s) salvos no cache do seu perfil!")
                    st.rerun()

    cached_projects = prof.get("cached_repos", [])
    if cached_projects:
        with st.expander(f"📦 Projetos do GitHub em Cache ({len(cached_projects)} repositórios)", expanded=False):
            for r in cached_projects:
                st.markdown(f"- **{r.get('name')}** ({r.get('language') or 'Sem linguagem'}): {r.get('description') or 'Sem descrição'}")

    st.markdown("---")
    # 2. Banco de Dados / Persistência
    st.markdown("#### 2. Persistência de Dados (Supabase / Local)")
    db_status = db_migrator.check_or_setup_tables()
    is_supa = history_manager.is_supabase_configured()
    
    if is_supa:
        st.success("🟢 **Supabase Conectado:** Suas candidaturas, perfis e diagnósticos estão sendo salvos no banco de dados PostgreSQL na nuvem.")
        st.caption(f"Host: `{config.SUPABASE_URL[:25]}...`")
        if not db_status.get("user_profiles_ready"):
            st.warning("⚠️ A tabela `user_profiles` ainda não foi criada no Supabase. Execute o script `supabase_schema.sql` no SQL Editor do painel do Supabase para ativar perfis em nuvem.")
        
        c_sync, c_clean = st.columns(2)
        with c_sync:
            if st.button("🔄 Sincronizar Histórico Local com Supabase", help="Envia currículos locais que ainda não foram para a nuvem", width="stretch"):
                with st.spinner("Sincronizando..."):
                    n_sync = history_manager.sync_local_to_supabase()
                    clear_history_cache()
                    st.success(f"{n_sync} currículo(s) local(is) sincronizado(s) no Supabase!")
                    st.rerun()
        with c_clean:
            if st.button("🧹 Limpar Registros de Teste do Supabase", help="Remove vagas criadas por testes como Staff AI Agent Engineer, etc.", width="stretch"):
                n_del = history_manager.clean_test_records_from_supabase()
                clear_history_cache()
                st.success(f"{n_del} registro(s) de teste removido(s) do Supabase!")
                st.rerun()
    else:
        st.info("🟡 **Armazenamento Local Ativo:** Os currículos estão sendo salvos como arquivos Markdown na pasta `history/`.")
        with st.expander("☁️ Como ativar o Supabase para Deploy na Nuvem (Streamlit Cloud)", expanded=False):
            st.markdown("""
            1. Crie uma conta gratuita em [supabase.com](https://supabase.com).
            2. Crie um novo projeto e execute o script **`supabase_schema.sql`** no SQL Editor.
            3. Adicione suas credenciais no `.env` (local) ou nos **Secrets** do Streamlit Community Cloud:
               ```toml
               SUPABASE_URL = "https://seu-projeto.supabase.co"
               SUPABASE_KEY = "sua-chave-anon"
               ```
            """)

    st.markdown("---")
    # 3. Provedores de IA & Economia de Tokens
    st.markdown("#### 3. Inteligência Artificial & Consumo de Tokens")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Modelo Ativo:** `{config.GEMINI_MODEL}`")
        if config.GEMINI_API_KEY:
            st.success("🟢 Chave GEMINI_API_KEY configurada.")
        else:
            st.error("🔴 GEMINI_API_KEY não configurada no `.env`.")
        if config.GROQ_API_KEY:
            st.success(f"🟢 Reserva Groq ativa: `{config.GROQ_MODEL}`")
        else:
            st.caption("⚪ GROQ_API_KEY não configurada (sem reserva quando a cota do Gemini acabar).")

    with c2:
        if config.GITHUB_TOKEN and "your_github_token" not in config.GITHUB_TOKEN:
            st.success("🟢 GITHUB_TOKEN configurado.")
        else:
            st.caption("⚪ GITHUB_TOKEN não configurado (opcional, consulta pública anônima ativa).")

    with st.expander("💡 Dicas para Economizar Tokens e Evitar Limite de Cota (429)", expanded=True):
        st.markdown("""
        - **Salve seu Currículo Base no Perfil:** Com o currículo base salvo, você não precisa reenviar o arquivo toda vez.
        - **Projetos em Cache:** O cache de repositórios do seu perfil evita consultas repetitivas ao GitHub e corta até 50% do tamanho do prompt enviado ao LLM.
        - **Desmarque a Cover Letter:** Ao gerar um currículo no assistente, desmarque a geração da carta se você precisa apenas do currículo. Isso economiza até 40% dos tokens por execução.
        - **Desmarque a Auditoria Rígida:** O modo econômico valida o currículo de forma ultra-rápida sem chamar uma segunda rodada de LLM.
        - **Use o modelo Flash-Lite:** Configure `GEMINI_MODEL=gemini-3.5-flash-lite` no seu `.env` para respostas instantâneas e menor custo de cota.
        """)

def main():
    selected_page = render_sidebar()
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    
    # Se estiver no modo de visualização de histórico
    if "viewing_history" in st.session_state:
        render_application_view(st.session_state.viewing_history)
        return
        
    resumes = get_cached_resumes(current_uid)
    
    if selected_page == "📊 Dashboard Executivo":
        render_dashboard(resumes)
    elif selected_page == "🚀 Nova Otimização (Wizard)":
        render_new_optimization()
    elif selected_page == "📚 Central de Candidaturas":
        render_applications_list(resumes)
    elif selected_page == "⚙️ Configurações & Status":
        render_settings()

if __name__ == "__main__":
    main()
