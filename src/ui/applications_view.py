import streamlit as st
from typing import Callable
from src.core import history_manager
from src.core.resume_formatter import format_resume_to_html
from src.agents.state import GraphState
from src.ui.diagnostic_view import render_ats_diagnostic_panel
from src.ui.navbar import clear_transient_state, set_page
from src.ui.components import page_header, login_gate, application_card

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
    job_title = (metadata.get("job_title") or "Vaga").strip()
    job_url = metadata.get("job_url", "")
    lang = (metadata.get("language") or "pt").upper()
    date_str = history_manager.format_display_date(metadata.get("date", ""))
    diagnostic = metadata.get("diagnostic", {})
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    is_rerun_open = st.session_state.get(f"show_rerun_{filepath}", False)

    # Barra de ações: voltar à esquerda, ações da candidatura à direita
    with st.container(horizontal=True, vertical_alignment="center"):
        if st.button("Todas as candidaturas", type="tertiary", icon=":material/arrow_back:"):
            if "viewing_history" in st.session_state:
                del st.session_state.viewing_history
            clear_transient_state()
            st.rerun()
        st.space("stretch")
        if st.button(
            "Fechar re-otimização" if is_rerun_open else "Re-otimizar com IA",
            icon=":material/close:" if is_rerun_open else ":material/autorenew:",
            type="secondary" if is_rerun_open else "primary"
        ):
            st.session_state[f"show_rerun_{filepath}"] = not is_rerun_open
            st.rerun()
        with st.popover("Excluir", icon=":material/delete:"):
            st.markdown("**Excluir esta candidatura?**")
            st.caption("Esta ação remove o currículo e diagnóstico permanentemente.")
            if st.button("Sim, excluir definitivamente", type="primary", icon=":material/delete_forever:", key=f"btn_confirm_del_{filepath}", width="stretch"):
                history_manager.delete_application(filepath)
                clear_history_cache_cb()
                if "viewing_history" in st.session_state:
                    del st.session_state.viewing_history
                st.toast("Candidatura excluída com sucesso!")
                clear_transient_state()
                st.rerun()

    # Painel interativo de Re-otimização
    if is_rerun_open:
        with st.container(border=True):
            st.markdown("#### :material/autorenew: Re-otimizar candidatura")
            st.caption("Re-execute o fluxo multi-agente ajustando a vaga, o currículo base ou as opções de IA.")
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                r_title = st.text_input("Título da vaga *", value=job_title, key=f"r_title_{filepath}")
            with col_r2:
                r_url = st.text_input("Link da vaga", value=job_url, key=f"r_url_{filepath}")

            r_github = st.text_input("Usuário do GitHub", value=metadata.get("github_username", ""), icon=":material/alternate_email:", key=f"r_gh_{filepath}")

            col_desc, col_base = st.columns(2)
            with col_desc:
                r_desc = st.text_area("Descrição completa da vaga *", value=metadata.get("job_description", ""), height=220, key=f"r_desc_{filepath}")
            with col_base:
                default_base = metadata.get("base_resume") or app_data.get("resume_md", "")
                r_base = st.text_area("Currículo base *", value=default_base, height=220, key=f"r_base_{filepath}")

            with st.container(horizontal=True, vertical_alignment="center"):
                r_cover = st.toggle("Gerar nova carta de apresentação", value=bool(app_data.get("cover_letter_md")), key=f"r_cov_{filepath}")
                r_strict = st.toggle("Auditoria rígida de qualidade", value=False, key=f"r_str_{filepath}")
                st.space("stretch")
                run_rerun = st.button("Executar re-otimização", type="primary", icon=":material/rocket_launch:", key=f"btn_run_rerun_{filepath}")

            if run_rerun:
                clear_transient_state()
                if not r_title or not r_desc or not r_base:
                    st.error("Preencha título, descrição e currículo base.", icon=":material/error:")
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
                        st.write("Reprocessando alinhamento com a vaga...")
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

    # Cabeçalho da vaga
    st.header(job_title, anchor=False)
    meta = [f":violet-badge[:material/calendar_today: {date_str}]", f":blue-badge[:material/translate: {lang}]"]
    if job_url:
        meta.append(f"[:material/open_in_new: Ver anúncio da vaga]({job_url})")
    st.markdown("  ".join(meta))

    techs = metadata.get("technologies", [])
    if techs:
        st.markdown(" ".join(f":gray-badge[{t}]" for t in techs))

    # Abas de Exibição de Conteúdo
    tab_diag, tab_a4, tab_cv, tab_letter = st.tabs([
        ":material/fact_check: Diagnóstico ATS",
        ":material/print: Currículo (A4)",
        ":material/code: Markdown",
        ":material/mail: Carta de apresentação"
    ])

    resume_md = app_data.get("resume_md", "")
    cover_letter_md = app_data.get("cover_letter_md", "")
    formatted_html = format_resume_to_html(resume_md, title=f"Currículo - {job_title}")
    file_stub = job_title.replace(" ", "_")

    with tab_diag:
        if diagnostic:
            render_ats_diagnostic_panel(diagnostic)
        else:
            st.info("Nenhum diagnóstico ATS foi registrado para esta aplicação.")

    with tab_a4:
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.download_button(
                label="Baixar HTML imprimível (salvar como PDF)",
                data=formatted_html,
                file_name=f"Curriculo_{file_stub}.html",
                mime="text/html",
                icon=":material/download:"
            )
        st.components.v1.html(formatted_html, height=1000, scrolling=True)

    with tab_cv:
        with st.container(horizontal=True, horizontal_alignment="right"):
            st.download_button(
                label="Baixar currículo (.md)",
                data=resume_md,
                file_name=f"Curriculo_{file_stub}.md",
                mime="text/markdown",
                icon=":material/download:"
            )
        with st.container(border=True):
            st.markdown(resume_md if resume_md else "_Nenhum conteúdo de currículo encontrado._")

    with tab_letter:
        if cover_letter_md:
            with st.container(horizontal=True, horizontal_alignment="right"):
                st.download_button(
                    label="Baixar carta (.md)",
                    data=cover_letter_md,
                    file_name=f"CoverLetter_{file_stub}.md",
                    mime="text/markdown",
                    icon=":material/download:"
                )
            with st.container(border=True):
                st.markdown(cover_letter_md)
        else:
            st.info("Esta aplicação não possui uma carta de apresentação gerada.")

def render_applications_list(resumes: list):
    """
    Renderiza a listagem de candidaturas com busca reativa.
    """
    actions = page_header("Candidaturas", "Todas as suas candidaturas, da mais recente para a mais antiga.")

    if not resumes:
        st.info("Nenhuma candidatura encontrada no histórico.", icon=":material/info:")
        return

    with actions:
        if st.button("Nova otimização", type="primary", icon=":material/add:", key="apps_btn_new", width="stretch"):
            set_page("wizard")
            st.rerun()

    search_query = st.text_input(
        "Buscar candidaturas",
        placeholder="Filtrar por vaga ou tecnologia — ex: Python, React, Senior",
        icon=":material/search:",
        label_visibility="collapsed"
    )

    filtered_resumes = resumes
    if search_query:
        q = search_query.lower()
        filtered_resumes = [
            r for r in resumes
            if q in r.get("job_title", "").lower() or any(q in t.lower() for t in r.get("technologies", []))
        ]

    st.caption(f"Exibindo {len(filtered_resumes)} de {len(resumes)} candidaturas")
    for idx, r in enumerate(filtered_resumes):
        application_card(r, key=f"hist_card_{idx}")

def render_applications_view(
    resumes: list,
    get_cached_application_fn: Callable,
    clear_history_cache_cb: Callable,
    graph
):
    """
    Roteador interno da seção de Candidaturas. Se houver visualização de item ativa,
    renderiza o detalhe; caso contrário, renderiza a lista.
    Protege o acesso a dados exigindo autenticação.
    """
    session = st.session_state.get("user_session", {})
    is_guest = session.get("is_guest", True)

    if is_guest:
        page_header("Candidaturas", "Seus currículos gerados, diagnósticos e cartas de apresentação.")
        login_gate(
            "Acesso Protegido",
            "Suas candidaturas, currículos gerados e cartas de apresentação são dados privados. "
            "Conecte-se à sua conta para visualizá-los e imprimi-los.",
            key="apps"
        )
        return

    if "viewing_history" in st.session_state and st.session_state.viewing_history:
        render_application_view(
            st.session_state.viewing_history,
            get_cached_application_fn,
            clear_history_cache_cb,
            graph
        )
    else:
        render_applications_list(resumes)
