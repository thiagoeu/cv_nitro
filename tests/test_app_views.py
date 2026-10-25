import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import app
from src.ui import dashboard_view, applications_view, wizard_view

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
        app.render_dashboard([])

        # Test settings
        app.render_settings()

        # Test empty applications list
        app.render_applications_list([])

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
        {"job_analyzer": {"job_keywords": ["FastAPI"], "job_technologies": ["Python"], "job_language": "pt"}},
        {"github_fetcher": {"raw_github_repos": [{"name": "fastapi-core"}]}},
        {"relevance_ranker": {"github_repos": [{"name": "fastapi-core"}]}},
        {"resume_generator": {"generated_resume_md": "# Currículo em Streaming"}},
        {"quality_reviewer": {"reviewer_approved": True, "diagnostic": {"ats_score": 90}}}
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
        assert mock_graph.stream.call_args[1]["stream_mode"] == "updates"
        assert mock_save.called
        save_kwargs = mock_save.call_args[1]
        assert save_kwargs["content"] == "# Currículo em Streaming"
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


