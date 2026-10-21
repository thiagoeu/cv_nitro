import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, profile_manager
from src.agents.state import GraphState
from src.ui.navbar import clear_transient_state, set_page
from src.ui.components import page_header, resume_input

def render_wizard_view(graph, clear_history_cache_cb: Optional[Callable] = None):
    """
    Renderiza o Assistente de Nova Otimização (Wizard) em 3 etapas desacopladas.
    Realiza auto-preenchimento via perfil e limpa erros transitórios antes do disparo.
    """
    page_header("Otimizador de currículo", "Três passos: seu currículo, a vaga e as preferências da IA.")

    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    current_email = st.session_state.user_session.get("email", "")
    user_prof = profile_manager.get_user_profile(current_uid, current_email)

    # ETAPA 1
    with st.container(border=True):
        st.markdown("#### :material/looks_one: Currículo base")
        if user_prof.get("base_resume"):
            st.caption(":green[:material/check_circle:] Carregado do seu **Perfil**. Edições aqui valem só para esta otimização.")
        else:
            st.caption("Dica: salve seu currículo no **Perfil** para ele vir preenchido automaticamente.")
        base_resume = resume_input("wizard_base_resume", user_prof.get("base_resume", ""), height=240)

    # ETAPA 2
    with st.container(border=True):
        st.markdown("#### :material/looks_two: Vaga alvo")
        col_vaga1, col_vaga2 = st.columns([2, 1])
        with col_vaga1:
            job_title = st.text_input("Título da vaga *", placeholder="Ex: Senior Python Engineer", key="wizard_job_title")
        with col_vaga2:
            job_url = st.text_input("Link da vaga", placeholder="https://linkedin.com/jobs/view/...", icon=":material/link:", key="wizard_job_url")

        github_user = st.text_input(
            "Usuário do GitHub (opcional, cruza seus projetos reais com a vaga)",
            value=user_prof.get("github_username", ""),
            placeholder="Ex: octocat",
            icon=":material/alternate_email:",
            key="wizard_github_user"
        )
        job_desc = st.text_area("Descrição completa da vaga *", height=200, placeholder="Cole aqui os requisitos e responsabilidades da vaga...", key="wizard_job_desc")

    # ETAPA 3
    with st.container(border=True):
        st.markdown("#### :material/looks_3: Preferências da IA")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            gen_cover = st.toggle(
                "Gerar carta de apresentação",
                value=True,
                help="Desative se você precisa apenas do currículo para economizar tokens."
            )
        with col_opt2:
            strict_rev = st.toggle(
                "Auditoria rígida de qualidade",
                value=False,
                help="Ative para auditoria com loop de refinamento; desative para modo econômico e resposta ultra-rápida."
            )

    # Erros de validação ficam junto do botão que os gerou
    if st.session_state.get("wizard_errors"):
        for err in st.session_state.wizard_errors:
            st.error(err, icon=":material/error:")

    submit = st.button("Gerar currículo otimizado e diagnóstico ATS", type="primary", icon=":material/rocket_launch:", width="stretch", key="wizard_submit_btn")

    if submit:
        # Purgar erros prévios
        clear_transient_state()

        errors = []
        if not job_title or not job_title.strip():
            errors.append("O título da vaga é obrigatório.")
        if not job_desc or not job_desc.strip():
            errors.append("A descrição da vaga é obrigatória.")
        if not base_resume or not base_resume.strip():
            errors.append("O currículo base do candidato é obrigatório.")

        if errors:
            st.session_state.wizard_errors = errors
            st.rerun()
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
            st.write("Analisando a vaga e identificando palavras-chave e idioma...")
            try:
                final_state = graph.invoke(initial_state)
            except Exception as e:
                status.update(label="Falha na execução", state="error", expanded=True)
                st.session_state.wizard_errors = [f"Erro durante a execução do grafo: {e}"]
                st.rerun()
                return
            status.update(label="Otimização concluída com sucesso!", state="complete", expanded=False)

        saved_path = history_manager.save_resume(
            job_title=job_title.strip(),
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
        if clear_history_cache_cb:
            clear_history_cache_cb()
        st.session_state[f"run_errors_{saved_path}"] = final_state.get("errors", [])
        st.session_state.viewing_history = saved_path
        set_page("applications", clear_transient=False)
        st.rerun()
