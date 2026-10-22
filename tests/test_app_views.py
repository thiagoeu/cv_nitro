import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import app
from src.ui import dashboard_view, applications_view

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

