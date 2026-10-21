import streamlit as st
import pandas as pd
from typing import Callable, Optional
from src.core import history_manager
from src.core.resume_formatter import format_resume_to_html
from src.agents.state import GraphState
from src.ui.diagnostic_view import render_ats_diagnostic_panel
from src.ui.navbar import clear_transient_state

def render_application_view(
    filepath: str,
    get_cached_application_fn: Callable,
    clear_history_cache_cb: Callable,
    graph
):
    """
    Renderiza o visualizador detalhado de uma candidatura selecionada.
    """
    app_data = get_cached_application_fn(filepath)
    metadata = app_data.get("metadata", {})
    job_title = metadata.get("job_title", "Vaga")
    job_url = metadata.get("job_url", "")
    lang = (metadata.get("language") or "pt").upper()
    date_str = history_manager.format_display_date(metadata.get("date", ""))
    diagnostic = metadata.get("diagnostic", {})
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    
    col_back, col_rerun, col_delete = st.columns([1.5, 2.5, 2.0])
    with col_back:
        if st.button("← Voltar à Lista", use_container_width=True):
            if "viewing_history" in st.session_state:
                del st.session_state.viewing_history
            clear_transient_state()
            st.rerun()
    with col_rerun:
        is_rerun_open = st.session_state.get(f"show_rerun_{filepath}", False)
        btn_label = "✖️ Fechar Re-otimização" if is_rerun_open else "🔄 Re-otimizar com IA"
        if st.button(btn_label, type="primary" if not is_rerun_open else "secondary", use_container_width=True):
            st.session_state[f"show_rerun_{filepath}"] = not is_rerun_open
            st.rerun()
    with col_delete:
        with st.popover("🗑️ Excluir", use_container_width=True):
            st.markdown("⚠️ **Excluir esta candidatura?**")
            st.caption("Esta ação remove o currículo e diagnóstico permanentemente.")
            if st.button("Sim, Excluir Definitivamente", type="primary", key=f"btn_confirm_del_{filepath}", use_container_width=True):
                history_manager.delete_application(filepath)
                clear_history_cache_cb()
                if "viewing_history" in st.session_state:
                    del st.session_state.viewing_history
                st.toast("Candidatura excluída com sucesso!")
                clear_transient_state()
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
                r_cover = st.checkbox("✉️ Gerar Nova Cover Letter", value=bool(app_data.get("cover_letter_md")), key=f"r_cov_{filepath}")
            with col_ropt2:
                r_strict = st.checkbox("🔍 Auditoria Rígida de Qualidade", value=False, key=f"r_str_{filepath}")
                
            if st.button("Executar Re-otimização 🚀", type="primary", use_container_width=True, key=f"btn_run_rerun_{filepath}"):
                clear_transient_state()
                if not r_title or not r_desc or not r_base:
                    st.error("Preencha título, descrição e currículo base.")
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
                    with st.status("Re-otimizando currículo...", expanded=True) as status:
                        st.write("🔍 Reprocessando alinhamento com a vaga...")
                        try:
                            final_state = graph.invoke(initial_state)
                        except Exception as e:
                            status.update(label="Falha na re-otimização", state="error")
                            st.error(f"Erro: {e}")
                            return
                        status.update(label="Re-otimização concluída!", state="complete", expanded=False)
                        
                    new_path = history_manager.save_resume(
                        job_title=r_title,
                        content=final_state.get("generated_resume_md", ""),
                        job_url=r_url,
                        cover_letter=final_state.get("generated_cover_letter_md", ""),
                        language=final_state.get("job_language", "pt"),
                        technologies=final_state.get("job_technologies", []),
                        job_description=r_desc,
                        base_resume=r_base,
                        github_username=r_github,
                        diagnostic=final_state.get("diagnostic", {}),
                        user_id=current_uid
                    )
                    clear_history_cache_cb()
                    st.session_state.viewing_history = new_path
                    st.session_state[f"show_rerun_{filepath}"] = False
                    st.toast("Currículo re-otimizado com sucesso!")
                    st.rerun()

    # Informações de cabeçalho da Vaga
    st.markdown(f"## {job_title}")
    caption_parts = [f"📅 **Data:** {date_str}", f"🌐 **Idioma:** `{lang}`"]
    if job_url:
        caption_parts.append(f"🔗 [Acessar Vaga no Site Original]({job_url})")
    st.markdown(" • ".join(caption_parts))
    
    # Tecnologias identificadas
    techs = metadata.get("technologies", [])
    if techs:
        st.markdown("**Tecnologias Mapeadas:** " + " ".join([f"`{t}`" for t in techs]))
        
    st.markdown("---")
    
    # Abas de Exibição de Conteúdo
    tab_diag, tab_a4, tab_cv, tab_letter = st.tabs([
        "📑 Diagnóstico ATS & Feedback",
        "🖨️ Formato A4 / Imprimível",
        "📝 Markdown Puro",
        "✉️ Carta de Apresentação"
    ])
    
    resume_md = app_data.get("resume_md", "")
    cover_letter_md = app_data.get("cover_letter_md", "")
    formatted_html = format_resume_to_html(resume_md, title=f"Currículo - {job_title}")
    
    with tab_diag:
        if diagnostic:
            render_ats_diagnostic_panel(diagnostic)
        else:
            st.info("Nenhum diagnóstico ATS foi registrado para esta aplicação.")
            
    with tab_a4:
        col_down_html, _ = st.columns([1, 2])
        with col_down_html:
            st.download_button(
                label="🖨️ Baixar HTML Imprimível (Salvar como PDF)",
                data=formatted_html,
                file_name=f"Curriculo_{job_title.replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
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

def render_applications_list(resumes: list):
    """
    Renderiza a listagem de candidaturas com busca e filtros reativos.
    """
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
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("##### 📄 Abrir Candidatura para Visualização e Impressão:")
    cols = st.columns(min(len(filtered_resumes), 3))
    for idx, r in enumerate(filtered_resumes[:6]):
        col = cols[idx % 3]
        job_label = r.get('job_title', 'Vaga')[:20]
        date_label = history_manager.format_display_date(r.get('date', ''))
        if col.button(f"📄 {job_label}\n({date_label})", key=f"hist_card_{idx}", use_container_width=True):
            st.session_state.viewing_history = r["filepath"]
            clear_transient_state()
            st.rerun()

def render_applications_view(
    resumes: list,
    get_cached_application_fn: Callable,
    clear_history_cache_cb: Callable,
    graph
):
    """
    Roteador interno da seção de Candidaturas. Se houver visualização de item ativa,
    renderiza o detalhe; caso contrário, renderiza a lista.
    """
    if "viewing_history" in st.session_state and st.session_state.viewing_history:
        render_application_view(
            st.session_state.viewing_history,
            get_cached_application_fn,
            clear_history_cache_cb,
            graph
        )
    else:
        render_applications_list(resumes)
