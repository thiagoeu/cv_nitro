import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import app
from src.ui import dashboard_view, applications_view, wizard_view, settings_view

def mock_columns(spec, *args, **kwargs):
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]

def test_app_views_smoke():
    st.session_state.clear()
    st.session_state.user_session = {"user_id": "u-123", "email": "test@user.com", "is_guest": False, "display_name": "Test User"}
    with patch("streamlit.sidebar.title"), \
         patch("streamlit.sidebar.caption"), \
         patch("streamlit.sidebar.markdown"), \
         patch("streamlit.sidebar.subheader"), \
         patch("src.core.history_manager.list_resumes", return_value=[]), \
         patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.info"), \
         patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.button"):
        
        # Test sidebar
        app.render_sidebar([])

        # Test empty dashboard
        dashboard_view.render_dashboard_view([])

        # Test settings
        settings_view.render_settings_view(MagicMock())

        # Test empty applications list
        applications_view.render_applications_list([])

def test_guest_restricted_views():
    # Usuário convidado (is_guest: True)
    st.session_state.clear()
    st.session_state.user_session = {"user_id": "guest_local", "email": "", "is_guest": True, "display_name": "Visitante"}
    
    with patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.warning") as mock_warn, \
         patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.button"):
        
        # 1. Dashboard bloqueia dados e exibe aviso de restrição
        dashboard_view.render_dashboard_view([])
        assert mock_warn.called
        assert "Exclusivo para Usuários Conectados" in mock_warn.call_args[0][0]
        
        # 2. Central de candidaturas bloqueia dados para convidados
        mock_warn.reset_mock()
        applications_view.render_applications_view([], MagicMock(), MagicMock(), MagicMock())
        assert mock_warn.called
        assert "Acesso Protegido" in mock_warn.call_args[0][0]

def test_application_view_edit_and_recompile_resume():
    st.session_state.clear()
    st.session_state.user_session = {
        "user_id": "usr-edit-1",
        "email": "dev@test.com",
        "is_guest": False,
        "display_name": "Dev User"
    }

    sample_app = {
        "metadata": {
            "job_title": "Python Specialist",
            "job_url": "https://vaga.com/123",
            "language": "pt",
            "date": "2026-10-21T10:00:00Z",
            "technologies": ["Python", "FastAPI"],
            "diagnostic": {"ats_score": 88}
        },
        "resume_md": "# Original Resume",
        "cover_letter_md": "Original Cover Letter"
    }

    mock_load_fn = MagicMock(return_value=sample_app)
    mock_clear_cache = MagicMock()

    def fake_button(label, **kwargs):
        # Dispara clique no botão de salvar e recompilar
        return "Salvar e Recompilar A4" in label

    mock_tabs = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    with patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.radio", return_value="Código Markdown Completo"), \
         patch("streamlit.text_area", return_value="# Modified & Recompiled Resume"), \
         patch("streamlit.tabs", return_value=mock_tabs), \
         patch("streamlit.download_button"), \
         patch("streamlit.components.v1.html"), \
         patch("streamlit.markdown"), \
         patch("streamlit.header"), \
         patch("streamlit.caption"), \
         patch("streamlit.space"), \
         patch("streamlit.container"), \
         patch("streamlit.expander"), \
         patch("streamlit.toast") as mock_toast, \
         patch("streamlit.rerun") as mock_rerun, \
         patch("src.core.history_manager.save_resume", return_value="supabase:new_uuid_123") as mock_save:

        applications_view.render_application_view(
            filepath="local/path/to/app.json",
            get_cached_application_fn=mock_load_fn,
            clear_history_cache_cb=mock_clear_cache,
            graph=MagicMock()
        )

        assert mock_save.called
        call_kwargs = mock_save.call_args[1]
        assert call_kwargs["job_title"] == "Python Specialist"
        assert call_kwargs["content"] == "# Modified & Recompiled Resume"
        assert mock_clear_cache.called
        assert mock_toast.called
        assert mock_rerun.called
        assert st.session_state.viewing_history == "supabase:new_uuid_123"

def test_application_view_edit_structured_fields():
    sample_app = {
        "metadata": {
            "job_title": "Full Stack Dev",
            "date": "2026-10-21T10:00:00Z"
        },
        "resume_md": "# Original Dev\n### Junior Dev\nSP | email@dev.com\n\n## EXPERIÊNCIA\nTexto anterior",
        "diagnostic": {}
    }

    mock_load_fn = MagicMock(return_value=sample_app)
    mock_clear_cache = MagicMock()

    def fake_button(label, **kwargs):
        return "Salvar e Recompilar A4" in label

    mock_tabs = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    with patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.radio", return_value="Campos Estruturados (Layout Travado)"), \
         patch("streamlit.text_input", side_effect=lambda label, value="", **kw: "Senior Architect" if "Cargo" in label else value), \
         patch("streamlit.text_area", return_value="Experiência ampliada com liderança"), \
         patch("streamlit.tabs", return_value=mock_tabs), \
         patch("streamlit.download_button"), \
         patch("streamlit.components.v1.html"), \
         patch("streamlit.markdown"), \
         patch("streamlit.header"), \
         patch("streamlit.caption"), \
         patch("streamlit.space"), \
         patch("streamlit.container"), \
         patch("streamlit.expander"), \
         patch("streamlit.info"), \
         patch("streamlit.toast") as mock_toast, \
         patch("streamlit.rerun") as mock_rerun, \
         patch("src.core.history_manager.save_resume", return_value="history/saved_app.md") as mock_save:

        applications_view.render_application_view(
            filepath="history/saved_app.md",
            get_cached_application_fn=mock_load_fn,
            clear_history_cache_cb=mock_clear_cache,
            graph=MagicMock()
        )

        assert mock_save.called
        call_kwargs = mock_save.call_args[1]
        assert "Senior Architect" in call_kwargs["content"]
        assert mock_clear_cache.called
        assert mock_toast.called
        assert mock_rerun.called

def test_application_view_edit_cover_letter():
    sample_app = {
        "metadata": {
            "job_title": "Frontend Lead",
            "date": "2026-10-21T10:00:00Z",
            "has_cover_letter": True
        },
        "resume_md": "# Frontend Lead Resume",
        "cover_letter_md": "Original Cover Letter",
        "diagnostic": {}
    }

    mock_load_fn = MagicMock(return_value=sample_app)
    mock_clear_cache = MagicMock()

    def fake_button(label, **kwargs):
        return "Salvar Carta de Apresentação" in label

    mock_tabs = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    with patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.text_area", return_value="Minha Carta Refinada Manualmente"), \
         patch("streamlit.tabs", return_value=mock_tabs), \
         patch("streamlit.download_button"), \
         patch("streamlit.components.v1.html"), \
         patch("streamlit.markdown"), \
         patch("streamlit.header"), \
         patch("streamlit.caption"), \
         patch("streamlit.space"), \
         patch("streamlit.container"), \
         patch("streamlit.expander"), \
         patch("streamlit.toast") as mock_toast, \
         patch("streamlit.rerun") as mock_rerun, \
         patch("src.core.history_manager.save_resume", return_value="history/saved_app.md") as mock_save:

        applications_view.render_application_view(
            filepath="history/saved_app.md",
            get_cached_application_fn=mock_load_fn,
            clear_history_cache_cb=mock_clear_cache,
            graph=MagicMock()
        )

        assert mock_save.called
        call_kwargs = mock_save.call_args[1]
        assert call_kwargs["job_title"] == "Frontend Lead"
        assert call_kwargs["cover_letter"] == "Minha Carta Refinada Manualmente"
        assert mock_clear_cache.called
        assert mock_toast.called
        assert mock_rerun.called
        assert st.session_state.viewing_history == "history/saved_app.md"

def test_wizard_view_streaming_success():
    st.session_state.clear()
    st.session_state.user_session = {
        "user_id": "usr-wizard-1",
        "email": "dev@test.com",
        "is_guest": False
    }

    mock_graph = MagicMock()
    # Emite eventos simulando streaming do grafo
    stream_events = [
        ("updates", {"job_analyzer": {"job_keywords": ["FastAPI"], "job_technologies": ["Python"], "job_language": "pt"}}),
        ("updates", {"github_fetcher": {"raw_github_repos": [{"name": "fastapi-core"}]}}),
        ("updates", {"relevance_ranker": {"github_repos": [{"name": "fastapi-core"}]}}),
        ("updates", {"resume_generator": {"generated_resume_md": "# Currículo em Streaming"}}),
        ("updates", {"quality_reviewer": {"reviewer_approved": True, "diagnostic": {"ats_score": 90}}}),
        ("values", {"generated_resume_md": "# Currículo em Streaming", "job_language": "pt",
                    "diagnostic": {"ats_score": 90}, "errors": ["Usuário 'x' não foi encontrado no GitHub (HTTP 404)."]})
    ]
    mock_graph.stream.return_value = iter(stream_events)

    def fake_button(label, **kwargs):
        return "Gerar currículo otimizado" in label

    def fake_text_input(label, **kwargs):
        if "Título" in label:
            return "Desenvolvedor Backend Python"
        if "Link" in label:
            return "https://vaga.com/1"
        return "candidato-github"

    with patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.text_input", side_effect=fake_text_input), \
         patch("streamlit.text_area", return_value="Requisitos: Python, FastAPI e microsserviços"), \
         patch("src.ui.components.resume_input", return_value="# Meu Currículo Base"), \
         patch("src.core.profile_manager.get_user_profile", return_value={"base_resume": "# Base", "github_username": "candidato"}), \
         patch("streamlit.toggle", return_value=True), \
         patch("streamlit.status") as mock_status, \
         patch("streamlit.empty") as mock_empty, \
         patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.container"), \
         patch("streamlit.rerun") as mock_rerun, \
         patch("src.core.history_manager.save_resume", return_value="history/saved_streaming.md") as mock_save:

        wizard_view.render_wizard_view(graph=mock_graph)

        assert mock_graph.stream.called
        assert mock_graph.stream.call_args[1]["stream_mode"] == ["updates", "values"]
        assert mock_save.called
        save_kwargs = mock_save.call_args[1]
        assert save_kwargs["content"] == "# Currículo em Streaming"
        assert save_kwargs["diagnostic"]["run_warnings"] == ["Usuário 'x' não foi encontrado no GitHub (HTTP 404)."]
        assert save_kwargs["job_title"] == "Desenvolvedor Backend Python"
        assert st.session_state.current_page == "applications"
        assert mock_rerun.called

def test_wizard_view_streaming_exception_handling():
    st.session_state.clear()
    st.session_state.user_session = {
        "user_id": "usr-wizard-err",
        "email": "err@test.com",
        "is_guest": False
    }

    mock_graph = MagicMock()
    # Simula falha catastrófica durante o streaming
    mock_graph.stream.side_effect = RuntimeError("Erro de conexão com cluster de LLM")

    def fake_button(label, **kwargs):
        return "Gerar currículo otimizado" in label

    with patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.text_input", return_value="Dev"), \
         patch("streamlit.text_area", return_value="Desc"), \
         patch("src.ui.components.resume_input", return_value="Base"), \
         patch("src.core.profile_manager.get_user_profile", return_value={}), \
         patch("streamlit.toggle", return_value=True), \
         patch("streamlit.status"), \
         patch("streamlit.empty"), \
         patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.container"), \
         patch("streamlit.rerun") as mock_rerun:

        wizard_view.render_wizard_view(graph=mock_graph)

        assert "wizard_errors" in st.session_state
        assert any("Erro durante a execução do grafo" in err for err in st.session_state.wizard_errors)
        assert mock_rerun.called



def test_run_pipeline_keeps_errors_from_every_node():
    import operator
    from typing import Annotated, TypedDict
    from langgraph.graph import StateGraph, START, END

    class State(TypedDict):
        x: int
        errors: Annotated[list, operator.add]

    g = StateGraph(State)
    g.add_node("a", lambda s: {"errors": ["a falhou"]})
    g.add_node("b", lambda s: {"errors": ["b falhou"]})
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)

    seen = []
    final = wizard_view.run_pipeline(g.compile(), {"x": 1, "errors": []}, lambda node, update: seen.append(node))
    assert final["errors"] == ["a falhou", "b falhou"]
    assert seen == ["a", "b"]

def test_build_initial_state_reuses_profile_repo_cache():
    cached = [{"name": "repo", "html_url": "https://github.com/octo/repo"}]
    profile = {"github_username": "Octo", "cached_repos": cached + [{"name": "formato-antigo", "url": "x"}]}
    state = wizard_view.build_initial_state("vaga", "cv", "octo", "", True, False, profile)
    assert state["raw_github_repos"] == cached
    assert "raw_github_repos" not in wizard_view.build_initial_state("vaga", "cv", "outro", "", True, False, profile)
    old_only = {"github_username": "octo", "cached_repos": [{"name": "formato-antigo", "url": "x"}]}
    assert "raw_github_repos" not in wizard_view.build_initial_state("vaga", "cv", "octo", "", True, False, old_only)

def test_notify_saved_warns_when_cloud_sync_failed(monkeypatch):
    from src.ui.components import notify_saved
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: True)
    with patch("streamlit.toast") as mock_toast:
        notify_saved("history/arquivo_local.md", "ok")
        assert "não foi possível sincronizar" in mock_toast.call_args[0][0]
        notify_saved("supabase:abc", "Salvo!")
        assert mock_toast.call_args[0][0] == "Salvo!"



def test_settings_view_quota_monitor_bars_and_warning(monkeypatch):
    from src.core import quota_manager, config

    st.session_state.clear()
    st.session_state.user_session = {"user_id": "u-quota", "email": "q@test.com", "is_guest": False}

    monkeypatch.setattr(config, "GEMINI_DAILY_TOKEN_LIMIT", 10000)
    monkeypatch.setattr(config, "GEMINI_DAILY_REQUEST_LIMIT", 100)
    # Consome 90% da cota do Gemini -> 10% restante (crítico <= 15%)
    quota_manager.record_llm_usage(provider="gemini", tokens=9000, requests_count=10)

    def fake_button(label, **kwargs):
        return "Consultar cota GitHub" in label

    with patch("streamlit.markdown"), \
         patch("streamlit.caption"), \
         patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.container"), \
         patch("streamlit.expander"), \
         patch("streamlit.code"), \
         patch("streamlit.spinner"), \
         patch("streamlit.rerun"), \
         patch("streamlit.button", side_effect=fake_button), \
         patch("streamlit.progress") as mock_progress, \
         patch("streamlit.warning") as mock_warning, \
         patch("src.core.quota_manager.probe_live_llm_quotas", return_value={}), \
         patch("src.core.quota_manager.fetch_github_rate_limit", return_value={
             "ok": True,
             "limit": 5000,
             "remaining": 4500,
             "used": 500,
             "remaining_pct": 90,
             "reset_time": "15:30",
         }):

        settings_view.render_settings_view(MagicMock())

        # Deve renderizar barras para Gemini (10% = 0.1), Groq (100% = 1.0) e GitHub (90% = 0.9)
        assert mock_progress.call_count >= 3
        progress_values = [call.args[0] for call in mock_progress.call_args_list]
        assert 0.1 in progress_values
        assert 1.0 in progress_values
        assert 0.9 in progress_values

        # Deve emitir alerta preventivo de cota baixa (<= 15%)
        assert mock_warning.called
        warning_texts = " ".join(str(c.args[0]) for c in mock_warning.call_args_list)
        assert "10% restante" in warning_texts
