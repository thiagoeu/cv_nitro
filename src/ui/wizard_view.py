import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, profile_manager
from src.agents.state import GraphState
from src.ui.navbar import clear_transient_state, set_page
from src.ui.components import page_header, resume_input, notify_saved

NODE_STATUS_LABELS = {
    "job_analyzer": "🎯 Análise da vaga e extração de requisitos concluída",
    "github_fetcher": "🐙 Repositórios públicos consultados no GitHub",
    "relevance_ranker": "⚡ Ranqueamento determinístico de relevância do portfólio",
    "resume_generator": "✍️ Redação executiva do currículo de alta fidelidade",
    "section_patcher": "🩹 Refinamento cirúrgico de seção concluído",
    "quality_reviewer": "🔍 Auditoria de qualidade e conformidade ATS",
    "cover_letter_generator": "✉️ Redação personalizada da Carta de Apresentação"
}

def build_initial_state(
    job_description: str,
    base_resume: str,
    github_username: str,
    job_url: str,
    generate_cover_letter: bool,
    strict_review: bool,
    profile: Optional[dict] = None
) -> dict:
    """Estado inicial do grafo; reaproveita os repositórios em cache do perfil quando o usuário do GitHub é o mesmo."""
    state = GraphState(
        job_description=job_description,
        base_resume_md=base_resume,
        github_username=github_username,
        job_url=job_url,
        job_keywords=[],
        job_technologies=[],
        job_language="pt",
        github_repos=[],
        github_readmes={},
        verified_technologies=None,
        unmatched_gaps=None,
        generated_resume_md=None,
        generated_cover_letter_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0,
        generate_cover_letter=generate_cover_letter,
        strict_review=strict_review,
        best_resume_md=None,
        best_ats_score=None,
        best_diagnostic=None,
        stop_reason=None,
        agent_trace=[]
    )
    profile = profile or {}
    same_user = (github_username or "").strip().lower() == (profile.get("github_username") or "").strip().lower()
    # Entradas sem html_url são do formato antigo do cache (já ranqueado): ignoradas, força busca normal
    cached = [r for r in profile.get("cached_repos") or [] if r.get("html_url")]
    if same_user and cached and github_username.strip():
        state["raw_github_repos"] = cached
    return state

def run_pipeline(graph, inputs: dict, on_node: Optional[Callable[[str, dict], None]] = None) -> dict:
    """
    Executa o grafo com streaming: 'updates' alimenta o progresso (on_node) e o último 'values'
    é o estado final, com os reducers aplicados (ex.: 'errors' acumulado de todos os nós).
    """
    final_state = dict(inputs)
    for mode, chunk in graph.stream(inputs, stream_mode=["updates", "values"]):
        if mode == "values":
            final_state = chunk
        elif on_node:
            for node_name, update in chunk.items():
                on_node(node_name, update if isinstance(update, dict) else {})
    return final_state

def run_pipeline_with_status(graph, inputs: dict, label: str) -> dict:
    """Checklist dos agentes e prévia do currículo enquanto o grafo roda; exceções são propagadas."""
    with st.status(label, expanded=True) as status:
        preview_placeholder = st.empty()

        def on_node(node_name: str, update: dict):
            st.write(NODE_STATUS_LABELS.get(node_name, f"Etapa {node_name} concluída."))
            if update.get("generated_resume_md"):
                with preview_placeholder.container():
                    st.caption("📄 *Prévia em tempo real do currículo gerado:*")
                    st.markdown(update["generated_resume_md"])

        try:
            final_state = run_pipeline(graph, inputs, on_node)
        except Exception:
            status.update(label="Falha na execução do pipeline", state="error", expanded=True)
            raise
        status.update(label="Otimização concluída com sucesso!", state="complete", expanded=False)
    return final_state

def save_pipeline_result(final_state: dict, job_title: str, job_url: str, job_description: str,
                         base_resume: str, github_username: str, user_id: str) -> str:
    """Salva a candidatura gerada; avisos não fatais, rastro e telemetria da execução ficam no diagnóstico (visíveis ao reabrir)."""
    diagnostic = dict(final_state.get("diagnostic") or {})
    if final_state.get("errors"):
        diagnostic["run_warnings"] = list(final_state["errors"])
    if final_state.get("agent_trace"):
        diagnostic["agent_trace"] = list(final_state["agent_trace"])
    if final_state.get("stop_reason"):
        diagnostic["stop_reason"] = final_state["stop_reason"]
    return history_manager.save_resume(
        job_title=job_title,
        content=final_state.get("generated_resume_md") or "",
        job_url=job_url,
        cover_letter=final_state.get("generated_cover_letter_md") or "",
        language=final_state.get("job_language") or "pt",
        technologies=final_state.get("job_technologies") or [],
        job_description=job_description,
        base_resume=base_resume,
        github_username=github_username,
        diagnostic=diagnostic,
        user_id=user_id
    )

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

        initial_state = build_initial_state(job_desc, base_resume, github_user, job_url, gen_cover, strict_rev, user_prof)

        try:
            final_state = run_pipeline_with_status(graph, initial_state, "Executando pipeline multi-agente em tempo real...")
        except Exception as e:
            st.session_state.wizard_errors = [f"Erro durante a execução do grafo: {e}"]
            st.rerun()
            return

        saved_path = save_pipeline_result(final_state, job_title.strip(), job_url, job_desc, base_resume, github_user, current_uid)
        if clear_history_cache_cb:
            clear_history_cache_cb()
        notify_saved(saved_path, "Currículo otimizado salvo!")
        st.session_state.viewing_history = saved_path
        set_page("applications", clear_transient=False)
        st.rerun()
