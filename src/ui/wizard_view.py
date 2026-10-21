import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, profile_manager
from src.core.document_parser import extract_text_from_file
from src.agents.state import GraphState
from src.ui.navbar import clear_transient_state

def render_wizard_view(graph, clear_history_cache_cb: Optional[Callable] = None):
    """
    Renderiza o Assistente de Nova Otimização (Wizard) em 3 etapas desacopladas.
    Realiza auto-preenchimento via perfil e limpa erros transitórios antes do disparo.
    """
    st.markdown("### 🚀 Assistente de Otimização de Currículo")
    st.caption("Preencha as informações abaixo passo a passo para a IA analisar a vaga e estruturar o melhor currículo ATS.")
    
    # Exibe erros transitórios se houver
    if st.session_state.get("wizard_errors"):
        for err in st.session_state.wizard_errors:
            st.error(f"⚠️ {err}")

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
    submit = st.button("Gerar Currículo Otimizado & Diagnóstico ATS 🚀", type="primary", use_container_width=True, key="wizard_submit_btn")
    
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
            st.write("🔍 Analisando a vaga e identificando palavras-chave e idioma...")
            try:
                final_state = graph.invoke(initial_state)
            except Exception as e:
                status.update(label="Falha na execução", state="error", expanded=True)
                st.session_state.wizard_errors = [f"Erro durante a execução do grafo: {e}"]
                st.rerun()
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
        if clear_history_cache_cb:
            clear_history_cache_cb()
        st.session_state[f"run_errors_{saved_path}"] = final_state.get("errors", [])
        st.session_state.viewing_history = saved_path
        st.session_state.current_page = "applications"
        st.rerun()
