import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, config, db_migrator
from src.ui.components import page_header

def _status(ok: bool, label: str, detail: str = ""):
    """Linha de status padronizada: badge verde/cinza + descrição."""
    badge = ":green-badge[:material/check_circle: Ativo]" if ok else ":gray-badge[:material/radio_button_unchecked: Inativo]"
    st.markdown(f"{badge} **{label}**" + (f"  \n:gray[{detail}]" if detail else ""))

def render_settings_view(clear_history_cache_cb: Optional[Callable] = None):
    """
    Renderiza a tela de status do sistema: banco de dados e provedores de IA.
    """
    page_header("Sistema", "Status das integrações: banco de dados, provedores de IA e GitHub.")

    db_status = db_migrator.check_or_setup_tables()
    is_supa = history_manager.is_supabase_configured()

    col_db, col_ai = st.columns(2, gap="medium")

    # 1. Banco de Dados / Persistência
    with col_db:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/database: Armazenamento")
            if is_supa:
                _status(True, "Supabase conectado", f"Candidaturas, perfis e diagnósticos salvos no PostgreSQL · {config.SUPABASE_URL[:25]}...")
                if not db_status.get("user_profiles_ready"):
                    st.warning("A tabela `user_profiles` ainda não existe. Execute o script SQL abaixo no painel do Supabase.", icon=":material/warning:")

                with st.container(horizontal=True):
                    if st.button("Sincronizar histórico local", icon=":material/cloud_upload:", help="Envia currículos locais que ainda não foram para a nuvem"):
                        with st.spinner("Sincronizando..."):
                            n_sync = history_manager.sync_local_to_supabase()
                            if clear_history_cache_cb:
                                clear_history_cache_cb()
                            st.success(f"{n_sync} currículo(s) local(is) sincronizado(s) no Supabase!")
                            st.rerun()
                    if st.button("Limpar registros de teste", icon=":material/cleaning_services:", help="Remove vagas criadas por testes"):
                        n_del = history_manager.clean_test_records_from_supabase()
                        if clear_history_cache_cb:
                            clear_history_cache_cb()
                        st.success(f"{n_del} registro(s) de teste removido(s) do Supabase!")
                        st.rerun()
            else:
                _status(False, "Supabase", "Usando armazenamento local: currículos salvos como Markdown na pasta history/.")

    # 2. Provedores de IA & GitHub
    with col_ai:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/psychology: IA e integrações")
            _status(bool(config.GEMINI_API_KEY), f"Gemini · {config.GEMINI_MODEL}", "" if config.GEMINI_API_KEY else "Defina GEMINI_API_KEY no .env")
            _status(bool(config.GROQ_API_KEY), f"Groq (reserva) · {config.GROQ_MODEL}", "" if config.GROQ_API_KEY else "Sem reserva quando a cota do Gemini acabar")
            gh_ok = bool(config.GITHUB_TOKEN) and "your_github_token" not in config.GITHUB_TOKEN
            _status(gh_ok, "GitHub token", "" if gh_ok else "Opcional: sem ele a consulta é pública e anônima")

    with st.expander("Script de migração e RLS do Supabase (SQL Editor)", icon=":material/terminal:", expanded=not is_supa or not db_status.get("user_profiles_ready")):
        st.markdown("""
        Copie o script abaixo e cole no **SQL Editor** do painel Supabase para:
        1. Criar tabelas com proteção RLS estrita (`auth.uid() = user_id`).
        2. Ativar o trigger que inicializa automaticamente perfis quando novos usuários se cadastram.
        """)
        st.code(db_status.get("sql_script") or db_migrator.get_schema_sql(), language="sql")

    with st.expander("Dicas para economizar tokens e evitar limite de cota (429)", icon=":material/lightbulb:"):
        st.markdown("""
        - **Salve seu currículo base no Perfil:** você não precisa reenviar o arquivo toda vez.
        - **Projetos em cache:** o cache de repositórios do Perfil evita consultas repetidas ao GitHub e corta até 50% do prompt enviado ao LLM.
        - **Desative a carta de apresentação** quando precisar só do currículo: economiza até 40% dos tokens por execução.
        - **Desative a auditoria rígida:** o modo econômico valida o currículo sem uma segunda rodada de LLM.
        - **Use o modelo Flash-Lite:** configure `GEMINI_MODEL=gemini-3.5-flash-lite` no `.env` para respostas mais rápidas e menor custo de cota.
        """)
