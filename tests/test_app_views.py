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
