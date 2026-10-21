import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, config, profile_manager, db_migrator
from src.ui.navbar import clear_transient_state

def render_settings_view(clear_history_cache_cb: Optional[Callable] = None):
    """
    Renderiza a tela de configurações, perfil do usuário, banco de dados e provedores de IA.
    """
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
        if st.button("💾 Salvar Perfil do Candidato", type="primary", use_container_width=True, key="btn_save_profile"):
            clear_transient_state()
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
        if st.button("🔄 Atualizar Cache do GitHub", use_container_width=True, key="btn_sync_gh_cache", help="Busca seus repositórios no GitHub para alimentar o cache de economia de tokens"):
            clear_transient_state()
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
    # 2. Banco de Dados / Persistência & Assistente Supabase
    st.markdown("#### 🗄️ Persistência de Dados & Migração Supabase")
    db_status = db_migrator.check_or_setup_tables()
    is_supa = history_manager.is_supabase_configured()
    
    if is_supa:
        st.success("🟢 **Supabase Conectado:** Suas candidaturas, perfis e diagnósticos estão sendo salvos no banco de dados PostgreSQL na nuvem.")
        st.caption(f"Host: `{config.SUPABASE_URL[:25]}...`")
        if not db_status.get("user_profiles_ready"):
            st.warning("⚠️ A tabela `user_profiles` ainda não foi criada no Supabase. Execute o script abaixo no SQL Editor do painel.")
        
        c_sync, c_clean = st.columns(2)
        with c_sync:
            if st.button("🔄 Sincronizar Histórico Local com Supabase", help="Envia currículos locais que ainda não foram para a nuvem", use_container_width=True):
                with st.spinner("Sincronizando..."):
                    n_sync = history_manager.sync_local_to_supabase()
                    if clear_history_cache_cb:
                        clear_history_cache_cb()
                    st.success(f"{n_sync} currículo(s) local(is) sincronizado(s) no Supabase!")
                    st.rerun()
        with c_clean:
            if st.button("🧹 Limpar Registros de Teste do Supabase", help="Remove vagas criadas por testes", use_container_width=True):
                n_del = history_manager.clean_test_records_from_supabase()
                if clear_history_cache_cb:
                    clear_history_cache_cb()
                st.success(f"{n_del} registro(s) de teste removido(s) do Supabase!")
                st.rerun()
    else:
        st.info("🟡 **Armazenamento Local Ativo:** Os currículos estão sendo salvos como arquivos Markdown na pasta `history/`.")

    with st.expander("🛠️ Script de Migração & RLS do Supabase (SQL Editor)", expanded=not is_supa or not db_status.get("user_profiles_ready")):
        st.markdown("""
        Copie o script SQL abaixo e cole no **SQL Editor** do seu painel Supabase para:
        1. Criar tabelas com proteção RLS estrita (`auth.uid() = user_id`).
        2. Ativar o trigger que inicializa automaticamente perfis quando novos usuários se cadastram.
        """)
        schema_sql = db_status.get("sql_script") or db_migrator.get_schema_sql()
        st.code(schema_sql, language="sql")

    st.markdown("---")
    # 3. Provedores de IA & Economia de Tokens
    st.markdown("#### 🧠 Inteligência Artificial & Consumo de Tokens")
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
