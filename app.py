import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime

from src.core import history_manager
from src.core.document_parser import extract_text_from_file
from src.core.resume_formatter import format_resume_to_html
from src.agents.graph import build_graph
from src.agents.state import GraphState

# Configuração da página
st.set_page_config(
    page_title="GitMatch - CV Nitro Optimizer & Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializando o grafo
@st.cache_resource
def get_graph():
    return build_graph()

graph = get_graph()

def render_sidebar():
    st.sidebar.title("📚 Histórico Rápido")
    st.sidebar.caption("Suas candidaturas salvas")
    st.sidebar.markdown("---")
    
    resumes = history_manager.list_resumes()
    
    if not resumes:
        st.sidebar.info("Nenhuma candidatura no histórico.")
        return
        
    for idx, resume in enumerate(resumes[:15]):
        date_str = str(resume.get('date', ''))[:10]
        job_title = resume.get('job_title', 'Vaga Desconhecida')
        lang = (resume.get('language') or 'pt').upper()
        
        btn_label = f"[{lang}] {job_title} ({date_str})"
        if st.sidebar.button(btn_label, key=f"sidebar_hist_{idx}", width="stretch"):
            st.session_state.viewing_history = resume['filepath']
            st.rerun()

def render_application_view(filepath: str):
    if hasattr(history_manager, "load_application"):
        app_data = history_manager.load_application(filepath)
    else:
        app_data = {
            "resume_md": history_manager.load_resume(filepath),
            "cover_letter_md": "",
            "metadata": {}
        }
    metadata = app_data.get("metadata", {})
    job_title = metadata.get("job_title", "Vaga")
    job_url = metadata.get("job_url", "")
    lang = (metadata.get("language") or "pt").upper()
    date_str = str(metadata.get("date", ""))[:19].replace("T", " ")
    
    col_back, col_rerun, col_spacer = st.columns([1.5, 2.5, 3.5])
    with col_back:
        if st.button("← Voltar ao Início", width="stretch"):
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
        with st.expander("⚡ Re-otimizar Candidatura com o Novo Modelo de IA", expanded=True):
            st.info("Execute novamente o pipeline multi-agente para esta vaga utilizando o modelo atualizado de IA.")
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
                placeholder="Cole a descrição da vaga aqui para a IA analisar...",
                key=f"r_desc_{filepath}"
            )
            
            default_base = metadata.get("base_resume") or app_data.get("resume_md", "")
            r_base = st.text_area(
                "Currículo Base do Candidato *",
                value=default_base,
                height=180,
                key=f"r_base_{filepath}"
            )
            
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
                        review_attempts=0
                    )
                    with st.status("Re-executando fluxo multi-agente...", expanded=True) as status:
                        st.write("🔍 Analisando vaga e portfólio com o modelo de IA...")
                        try:
                            final_state = graph.invoke(initial_state)
                            status.update(label="Re-otimização concluída com sucesso!", state="complete", expanded=False)
                            
                            new_resume_md = final_state.get("generated_resume_md", "")
                            new_cover_md = final_state.get("generated_cover_letter_md", "")
                            new_lang = final_state.get("job_language", "pt")
                            new_techs = final_state.get("job_technologies", [])
                            
                            # Atualiza o arquivo existente com a nova versão gerada
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
                                filepath=filepath
                            )
                            st.session_state[f"show_rerun_{filepath}"] = False
                            st.success("Currículo e Cover Letter re-otimizados e salvos com sucesso!")
                            st.rerun()
                        except Exception as e:
                            status.update(label="Falha na re-otimização", state="error", expanded=True)
                            st.error(f"Erro durante a execução: {e}")
            
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
    
    # Abas com Currículo e Carta
    tab_a4, tab_cv, tab_letter = st.tabs([
        "📑 Folha Formatada (A4 / Impressão)",
        "📄 Markdown Puro",
        "✉️ Carta de Apresentação (Cover Letter)"
    ])
    
    resume_md = app_data.get("resume_md", "")
    cover_letter_md = app_data.get("cover_letter_md", "")
    formatted_html = format_resume_to_html(resume_md, job_title)
    
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
        st.components.v1.html(formatted_html, height=1000, scrolling=True)
        
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
    st.caption("Visão consolidada do seu funil e histórico de aplicações.")
    
    if not resumes:
        st.info("Nenhuma candidatura registrada ainda. Vá para a aba **🚀 Nova Otimização** para gerar seu primeiro currículo!")
        return

    # Cálculos das Métricas
    total_apps = len(resumes)
    en_apps = sum(1 for r in resumes if str(r.get("language", "")).lower() == "en")
    pt_apps = sum(1 for r in resumes if str(r.get("language", "")).lower() != "en")
    
    all_techs = []
    for r in resumes:
        all_techs.extend(r.get("technologies", []))
    tech_counter = Counter([t.strip().capitalize() for t in all_techs if t.strip()])
    
    # Cards de Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Aplicações", total_apps)
    m2.metric("Vagas em Inglês (EN)", en_apps)
    m3.metric("Vagas em Português (PT)", pt_apps)
    m4.metric("Tecnologias Únicas Mapeadas", len(tech_counter))
    
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
    st.markdown("##### 📋 Tabela de Vagas Aplicadas")
    
    # Lista detalhada em formato de tabela interativa
    table_rows = []
    for r in resumes:
        date_fmt = str(r.get("date", ""))[:16].replace("T", " ")
        raw_url = r.get("job_url", "")
        valid_url = raw_url if (raw_url and (raw_url.startswith("http://") or raw_url.startswith("https://"))) else None
        table_rows.append({
            "Vaga": r.get("job_title", "Vaga"),
            "Idioma": (r.get("language") or "pt").upper(),
            "Data do Ajuste": date_fmt,
            "Link da Vaga": valid_url,
            "Cover Letter": "Sim" if r.get("has_cover_letter") else "Não",
            "_filepath": r.get("filepath")
        })
        
    df_table = pd.DataFrame(table_rows)
    
    # Renderizamos a tabela visual nativa e interativa
    st.dataframe(
        df_table[["Vaga", "Idioma", "Data do Ajuste", "Link da Vaga", "Cover Letter"]],
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
    
    st.markdown("###### 🔍 Ações Rápidas de Visualização:")
    cols_buttons = st.columns(min(len(resumes), 4))
    for i, r in enumerate(resumes[:4]):
        col_btn = cols_buttons[i % 4]
        job_t = r.get("job_title", "Vaga")
        if col_btn.button(f"Abrir: {job_t[:20]}...", key=f"dash_btn_{i}", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            st.rerun()

def render_new_optimization():
    st.markdown("### 🚀 Nova Otimização de Currículo")
    st.write("Faça o upload do seu currículo ou cole seu texto, informe os dados da vaga e deixe a IA cuidar do resto.")
    
    # Upload de arquivo de currículo
    st.markdown("#### 1. Seu Currículo Base")
    uploaded_file = st.file_uploader(
        "Faça upload do seu currículo existente (PDF, DOCX, Markdown ou TXT):",
        type=["pdf", "docx", "md", "txt"],
        help="O sistema extrairá o texto automaticamente preservando sua experiência."
    )
    
    extracted_text = ""
    if uploaded_file is not None:
        try:
            extracted_text = extract_text_from_file(uploaded_file)
            st.success(f"Texto extraído com sucesso de **{uploaded_file.name}** ({len(extracted_text)} caracteres).")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            
    # Área de texto com fallback ou edição do texto extraído
    base_resume = st.text_area(
        "Conteúdo do Currículo Base (você pode editar ou colar diretamente aqui):",
        value=extracted_text,
        height=220,
        placeholder="Cole seu currículo aqui ou faça o upload do arquivo acima..."
    )
    
    st.markdown("#### 2. Dados da Vaga")
    col_vaga1, col_vaga2 = st.columns([2, 1])
    with col_vaga1:
        job_title = st.text_input("Título da Vaga *", placeholder="Ex: Senior Python Engineer / Especialista em Dados")
    with col_vaga2:
        job_url = st.text_input("Link da Vaga (URL opcional)", placeholder="Ex: https://linkedin.com/jobs/view/...")
        
    github_user = st.text_input("Usuário do GitHub (opcional para cruzar projetos)", placeholder="Ex: octocat")
    job_desc = st.text_area("Descrição Completa da Vaga *", height=200, placeholder="Cole a descrição da vaga aqui (em português ou inglês)...")
    
    submit = st.button("Gerar Currículo & Cover Letter 🚀", type="primary", width="stretch")
    
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
            review_attempts=0
        )
        
        with st.status("Executando fluxo multi-agente...", expanded=True) as status:
            st.write("🔍 Analisando a vaga e identificando idioma e tecnologias...")
            try:
                final_state = graph.invoke(initial_state)
                status.update(label="Otimização concluída com sucesso!", state="complete", expanded=False)
                
                generated_md = final_state.get("generated_resume_md", "")
                generated_cover = final_state.get("generated_cover_letter_md", "")
                job_lang = final_state.get("job_language", "pt")
                job_techs = final_state.get("job_technologies", [])
                
                # Salva no histórico com todos os novos metadados
                saved_path = history_manager.save_resume(
                    job_title=job_title,
                    content=generated_md,
                    job_url=job_url,
                    cover_letter=generated_cover,
                    language=job_lang,
                    technologies=job_techs,
                    job_description=job_desc,
                    base_resume=base_resume,
                    github_username=github_user
                )
                
                st.success(f"Currículo e Cover Letter gerados no idioma: **{job_lang.upper()}**!")
                
                # Exibe abas de resultado
                res_tab_a4, res_tab1, res_tab2 = st.tabs([
                    "📑 Folha Formatada (A4 / Impressão)",
                    "📄 Markdown Puro",
                    "✉️ Carta de Apresentação (Cover Letter)"
                ])
                
                formatted_html = format_resume_to_html(generated_md, job_title)
                
                with res_tab_a4:
                    col_dl_h, _ = st.columns([1, 2])
                    with col_dl_h:
                        st.download_button(
                            "🖨️ Baixar HTML Imprimível (Salvar como PDF)",
                            data=formatted_html,
                            file_name=f"Curriculo_{job_title.replace(' ', '_')}.html",
                            mime="text/html",
                            width="stretch"
                        )
                    st.components.v1.html(formatted_html, height=1000, scrolling=True)

                with res_tab1:
                    st.download_button(
                        "📥 Baixar Currículo (.md)",
                        data=generated_md,
                        file_name=f"Curriculo_{job_title.replace(' ', '_')}.md",
                        mime="text/markdown"
                    )
                    st.markdown(generated_md)
                    
                with res_tab2:
                    if generated_cover:
                        st.download_button(
                            "📥 Baixar Cover Letter (.md)",
                            data=generated_cover,
                            file_name=f"CoverLetter_{job_title.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
                        st.markdown(generated_cover)
                    else:
                        st.info("Nenhuma carta de apresentação gerada.")
                        
            except Exception as e:
                status.update(label="Falha na execução", state="error", expanded=True)
                st.error(f"Erro durante a execução do grafo: {e}")

def main():
    st.title("🎯 GitMatch - CV Nitro")
    
    render_sidebar()
    
    # Se estiver no modo de visualização de histórico
    if "viewing_history" in st.session_state:
        render_application_view(st.session_state.viewing_history)
        return
        
    resumes = history_manager.list_resumes()
    
    tab_dash, tab_new = st.tabs(["📊 Dashboard de Aplicações", "🚀 Nova Otimização"])
    
    with tab_dash:
        render_dashboard(resumes)
        
    with tab_new:
        render_new_optimization()

if __name__ == "__main__":
    main()
