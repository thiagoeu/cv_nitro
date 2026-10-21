import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

from src.core import history_manager, config
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

def show_errors(errors: list):
    for err in errors or []:
        st.warning(f"⚠️ {err}")

def render_sidebar():
    st.sidebar.title("🎯 GitMatch - CV Nitro")
    st.sidebar.caption("Otimizador Multi-Agente & Diagnóstico ATS")
    st.sidebar.markdown("---")
    
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
    
    resumes = history_manager.list_resumes()
    if not resumes:
        st.sidebar.caption("Nenhuma candidatura salva ainda.")
    else:
        for idx, resume in enumerate(resumes[:8]):
            date_str = str(resume.get('date', ''))[:10]
            job_title = resume.get('job_title', 'Vaga Desconhecida')
            lang = (resume.get('language') or 'pt').upper()
            
            btn_label = f"[{lang}] {job_title[:16]}... ({date_str})"
            if st.sidebar.button(btn_label, key=f"sidebar_hist_{idx}", width="stretch"):
                st.session_state.viewing_history = resume['filepath']
                st.rerun()
                
    return page

def render_application_view(filepath: str):
    app_data = history_manager.load_application(filepath)
    metadata = app_data.get("metadata", {})
    job_title = metadata.get("job_title", "Vaga")
    job_url = metadata.get("job_url", "")
    lang = (metadata.get("language") or "pt").upper()
    date_str = str(metadata.get("date", ""))[:19].replace("T", " ")
    diagnostic = metadata.get("diagnostic", {})
    
    col_back, col_rerun, col_spacer = st.columns([1.5, 2.5, 3.5])
    with col_back:
        if st.button("← Voltar à Lista", width="stretch"):
            del st.session_state.viewing_history
            st.rerun()
    with col_rerun:
        is_rerun_open = st.session_state.get(f"show_rerun_{filepath}", False)
        btn_label = "✖️ Fechar Re-otimização" if is_rerun_open else "🔄 Re-otimizar com IA"
        if st.button(btn_label, type="primary" if not is_rerun_open else "secondary", width="stretch"):
            st.session_state[f"show_rerun_{filepath}"] = not is_rerun_open
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
                                diagnostic=new_diag
                            )
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
    st.caption("Visão executiva do seu funil e métricas de mercado.")
    
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
    st.markdown("##### 📋 Candidaturas Recentes")
    
    cols_buttons = st.columns(min(len(resumes), 4))
    for i, r in enumerate(resumes[:4]):
        col_btn = cols_buttons[i % 4]
        job_t = r.get("job_title", "Vaga")
        if col_btn.button(f"Abrir: {job_t[:18]}...", key=f"dash_btn_{i}", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            st.rerun()

def render_new_optimization():
    st.markdown("### 🚀 Assistente de Otimização de Currículo")
    st.caption("Preencha as informações abaixo passo a passo para a IA analisar a vaga e estruturar o melhor currículo ATS.")
    
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
            
    base_resume = st.text_area(
        "Texto do Currículo Base (edite ou cole diretamente aqui):",
        value=extracted_text,
        height=200,
        placeholder="Cole seu currículo aqui ou faça o upload do arquivo acima..."
    )
    
    st.markdown("---")
    # ETAPA 2
    st.markdown("#### 2. Informações da Vaga Alvo")
    col_vaga1, col_vaga2 = st.columns([2, 1])
    with col_vaga1:
        job_title = st.text_input("Título da Vaga *", placeholder="Ex: Senior Python Engineer / Especialista em Dados")
    with col_vaga2:
        job_url = st.text_input("Link da Vaga (URL opcional)", placeholder="Ex: https://linkedin.com/jobs/view/...")
        
    github_user = st.text_input("Usuário do GitHub (opcional para cruzar projetos reais)", placeholder="Ex: octocat")
    job_desc = st.text_area("Descrição Completa da Vaga *", height=180, placeholder="Cole aqui a descrição dos requisitos e responsabilidades da vaga...")
    
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
    submit = st.button("Gerar Currículo Otimizado & Diagnóstico ATS 🚀", type="primary", width="stretch")
    
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
            diagnostic=final_state.get("diagnostic", {})
        )
        st.session_state[f"run_errors_{saved_path}"] = final_state.get("errors", [])
        st.session_state.viewing_history = saved_path
        st.rerun()

def render_applications_list(resumes: list):
    st.markdown("### 📚 Central de Candidaturas")
    st.caption("Gerenciador completo de todas as suas candidaturas e currículos salvos.")
    
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
        date_fmt = str(r.get("date", ""))[:16].replace("T", " ")
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
        if col.button(f"Visualizar: {r.get('job_title', 'Vaga')[:22]}", key=f"hist_card_{idx}", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            st.rerun()

def render_settings():
    st.markdown("### ⚙️ Configurações & Status do Sistema")
    st.caption("Verifique o status das conexões com o banco de dados na nuvem e provedores de Inteligência Artificial.")
    
    # 1. Banco de Dados / Persistência
    st.markdown("#### 1. Persistência de Dados (Supabase / Local)")
    is_supa = history_manager.is_supabase_configured()
    if is_supa:
        st.success("🟢 **Supabase Conectado:** Suas candidaturas e diagnósticos estão sendo salvos no banco de dados PostgreSQL na nuvem.")
        st.caption(f"Host: `{config.SUPABASE_URL[:25]}...`")
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
    # 2. Provedores de IA & Economia de Tokens
    st.markdown("#### 2. Inteligência Artificial & Consumo de Tokens")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Modelo Ativo:** `{config.GEMINI_MODEL}`")
        if config.GEMINI_API_KEY:
            st.success("🟢 Chave GEMINI_API_KEY configurada.")
        else:
            st.error("🔴 GEMINI_API_KEY não configurada no `.env`.")
            
    with c2:
        if config.GITHUB_TOKEN and "your_github_token" not in config.GITHUB_TOKEN:
            st.success("🟢 GITHUB_TOKEN configurado.")
        else:
            st.caption("⚪ GITHUB_TOKEN não configurado (opcional, consulta pública anônima ativa).")

    with st.expander("💡 Dicas para Economizar Tokens e Evitar Limite de Cota (429)", expanded=True):
        st.markdown("""
        - **Desmarque a Cover Letter:** Ao gerar um currículo no assistente, desmarque a geração da carta se você precisa apenas do currículo. Isso economiza até 40% dos tokens por execução.
        - **Desmarque a Auditoria Rígida:** O modo econômico valida o currículo de forma ultra-rápida sem chamar uma segunda rodada de LLM.
        - **Use o modelo Flash-Lite:** Configure `GEMINI_MODEL=gemini-2.0-flash-lite` no seu `.env` para respostas instantâneas e menor custo de cota.
        """)

def main():
    selected_page = render_sidebar()
    
    # Se estiver no modo de visualização de histórico
    if "viewing_history" in st.session_state:
        render_application_view(st.session_state.viewing_history)
        return
        
    resumes = history_manager.list_resumes()
    
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
