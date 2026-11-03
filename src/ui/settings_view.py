import streamlit as st
from typing import Callable, Optional
from src.core import history_manager, config, db_migrator, quota_manager
from src.ui.components import page_header


def _status(ok: bool, label: str, detail: str = ""):
    """Linha de status padronizada: badge verde/cinza + descrição."""
    badge = ":green-badge[:material/check_circle: Ativo]" if ok else ":gray-badge[:material/radio_button_unchecked: Inativo]"
    st.markdown(f"{badge} **{label}**" + (f"  \n:gray[{detail}]" if detail else ""))


def _quota_health_badge(health: str, remaining_pct: int) -> str:
    """Retorna o badge visual correspondente à saúde da cota restante."""
    if health == "critical":
        return f":red-badge[:material/error: {remaining_pct}% disponível · Risco de 429]"
    if health == "warning":
        return f":orange-badge[:material/warning: {remaining_pct}% disponível · Atenção]"
    return f":green-badge[:material/bolt: {remaining_pct}% disponível · Uso seguro]"


def render_settings_view(clear_history_cache_cb: Optional[Callable] = None):
    """
    Renderiza a tela de status do sistema: banco de dados, provedores de IA e monitor de cota de tokens.
    """
    page_header("Sistema", "Status das integrações, consumo de tokens e capacidade restante das APIs.")

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

                if st.button("Sincronizar histórico local", icon=":material/cloud_upload:", help="Envia seus currículos locais que ainda não foram para a nuvem") is True:
                    with st.spinner("Sincronizando..."):
                        n_sync = history_manager.sync_local_to_supabase(st.session_state.user_session.get("user_id"))
                        if clear_history_cache_cb:
                            clear_history_cache_cb()
                        st.success(f"{n_sync} currículo(s) local(is) sincronizado(s) no Supabase!")
                        st.rerun()
            else:
                missing = ", ".join(f"`{name}`" for name in history_manager.missing_supabase_settings())
                _status(False, "Supabase", f"Usando armazenamento local (pasta history/). Para ativar a nuvem, defina no .env: {missing}.")

    # 2. Provedores de IA & GitHub
    with col_ai:
        with st.container(border=True, height="stretch"):
            st.markdown("#### :material/psychology: IA e integrações")
            _status(bool(config.GEMINI_API_KEY), f"Gemini · {config.GEMINI_MODEL}", "" if config.GEMINI_API_KEY else "Defina GEMINI_API_KEY no .env")
            _status(bool(config.GROQ_API_KEY), f"Groq (reserva) · {config.GROQ_MODEL}", "" if config.GROQ_API_KEY else "Sem reserva quando a cota do Gemini acabar")
            gh_ok = bool(config.GITHUB_TOKEN) and "your_github_token" not in config.GITHUB_TOKEN
            _status(gh_ok, "GitHub token", "" if gh_ok else "Opcional: sem ele a consulta é pública e anônima")

    # 3. Monitor de Cota & Capacidade de Tokens
    quota_status = quota_manager.get_quota_status()
    gem = quota_status["gemini"]
    grq = quota_status["groq"]

    with st.container(border=True):
        st.markdown("#### :material/monitoring: Monitor de Cota & Capacidade de Tokens (Hoje)")
        st.caption(
            "Acompanhe a porcentagem disponível de tokens e requisições diárias para saber se é seguro continuar gerando currículos sem erro HTTP 429."
        )

        col_q_gem, col_q_grq = st.columns(2, gap="medium")

        with col_q_gem:
            gem_badge = _quota_health_badge(gem["health"], gem["remaining_pct"])
            st.markdown(f"**Google Gemini (`{config.GEMINI_MODEL}`)**  \n{gem_badge}")
            st.progress(
                gem["remaining_pct"] / 100.0,
                text=f"{gem['remaining_pct']}% restante ({gem['used_pct']}% usado) · ~{gem['estimated_remaining_runs']} otimizações completas restantes hoje",
            )
            st.caption(
                f"Tokens hoje: {gem['used_tokens']:,} / {gem['token_limit']:,} ({gem['remaining_tokens_pct']}% livre) · "
                f"Requisições: {gem['used_requests']} / {gem['request_limit']} ({gem['remaining_requests_pct']}% livre)"
            )
            if gem.get("live_status"):
                st.caption(f":material/cloud_done: **Status na API Google:** {gem['live_status']}")

        with col_q_grq:
            grq_badge = _quota_health_badge(grq["health"], grq["remaining_pct"])
            st.markdown(f"**Groq Fallback (`{config.GROQ_MODEL}`)**  \n{grq_badge}")
            st.progress(
                grq["remaining_pct"] / 100.0,
                text=f"{grq['remaining_pct']}% restante ({grq['used_pct']}% usado) · ~{grq['estimated_remaining_runs']} otimizações em reserva hoje",
            )
            st.caption(
                f"Tokens hoje: {grq['used_tokens']:,} / {grq['token_limit']:,} ({grq['remaining_tokens_pct']}% livre) · "
                f"Requisições: {grq['used_requests']} / {grq['request_limit']} ({grq['remaining_requests_pct']}% livre · fonte: {grq.get('source', 'local')})"
            )
            if grq.get("live_status"):
                st.caption(f":material/cloud_done: **Status na API Groq:** {grq['live_status']}")

        if gem["remaining_pct"] <= 15:
            if config.GROQ_API_KEY:
                st.warning(
                    f"Capacidade diária do Gemini baixa ({gem['remaining_pct']}% restante). "
                    "As próximas execuções podem atingir limite HTTP 429 e alternar automaticamente para o Groq (reserva). "
                    "Para economizar cota, desative a carta de apresentação ou a auditoria rígida no Otimizador.",
                    icon=":material/warning:",
                )
            else:
                st.warning(
                    f"Capacidade diária do Gemini crítica ({gem['remaining_pct']}% restante) e o provedor reserva (Groq) não está configurado. "
                    "Há risco elevado de falha por limite de cota (HTTP 429) nas próximas gerações.",
                    icon=":material/error:",
                )

        col_gh_quota, col_btn_gh, col_btn_reset = st.columns([2, 1, 1], gap="small")

        with col_btn_gh:
            if st.button(
                "Consultar cota GitHub / APIs",
                icon=":material/sync:",
                help="Consulta ao vivo os servidores do Groq (headers x-ratelimit), GitHub (/rate_limit) e testa disponibilidade 200/429 no Gemini",
            ) is True:
                with st.spinner("Consultando APIs ao vivo..."):
                    st.session_state["gh_rate_limit"] = quota_manager.fetch_github_rate_limit()
                    quota_manager.probe_live_llm_quotas()
                st.rerun()

        with col_btn_reset:
            if st.button(
                "Zerar medidor diário",
                icon=":material/restart_alt:",
                help="Reinicia manualmente os contadores locais de tokens e requisições de hoje",
            ) is True:
                quota_manager.reset_daily_quota()
                st.toast("Medidor diário de tokens reiniciado!", icon=":material/check_circle:")
                st.rerun()

        with col_gh_quota:
            gh_rate = st.session_state.get("gh_rate_limit")
            if isinstance(gh_rate, dict):
                if gh_rate.get("ok"):
                    reset_info = f" · renova às {gh_rate['reset_time']}" if gh_rate.get("reset_time") else ""
                    st.progress(
                        gh_rate["remaining_pct"] / 100.0,
                        text=f"GitHub API: {gh_rate['remaining_pct']}% disponível ({gh_rate['remaining']}/{gh_rate['limit']} req/h{reset_info})",
                    )
                else:
                    st.caption(f":orange[Não foi possível consultar a cota do GitHub: {gh_rate.get('error', 'erro de rede')}]")
            else:
                st.caption("Clique em **Consultar cota GitHub / APIs** para buscar os limites reais nos servidores do Groq, GitHub e testar o Gemini.")

    with st.expander("Script de migração e RLS do Supabase (SQL Editor)", icon=":material/terminal:", expanded=not is_supa or not db_status.get("user_profiles_ready")):
        st.markdown("""
        Copie o script abaixo e cole no **SQL Editor** do painel Supabase para:
        1. Criar as tabelas com RLS fechado para a chave anon (o app acessa os dados com a service role, sempre filtrando por `user_id`).
        2. Exigir `user_id` em toda gravação nova.
        3. Ativar o trigger que inicializa automaticamente perfis quando novos usuários se cadastram.
        """)
        st.code(db_status.get("sql_script") or db_migrator.get_schema_sql(), language="sql")

    with st.expander("Dicas para economizar tokens e evitar limite de cota (429)", icon=":material/lightbulb:"):
        st.markdown("""
        - **Salve seu currículo base no Perfil:** você não precisa reenviar o arquivo toda vez.
        - **Projetos em cache:** com o mesmo usuário do GitHub do Perfil, o Otimizador usa a lista de repositórios em cache e pula a listagem na API do GitHub (os READMEs dos 3 selecionados ainda são baixados).
        - **Desative a carta de apresentação** quando precisar só do currículo: economiza até 40% dos tokens por execução.
        - **Desative a auditoria rígida:** o modo econômico valida o currículo sem uma segunda rodada de LLM.
        - **Use o modelo Flash-Lite:** configure `GEMINI_MODEL=gemini-3.5-flash-lite` no `.env` para respostas mais rápidas e menor custo de cota.
        """)
