import streamlit as st
from unittest.mock import patch, MagicMock
from src.ui import auth_views

def mock_columns(spec, *args, **kwargs):
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]

def test_render_login_view_structure():
    st.session_state.clear()
    with patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.markdown"), \
         patch("streamlit.form") as mock_form, \
         patch("streamlit.text_input") as mock_input, \
         patch("streamlit.form_submit_button", return_value=False), \
         patch("streamlit.button", return_value=False):
        
        mock_form.return_value.__enter__.return_value = None
        mock_form.return_value.__exit__.return_value = None
        
        auth_views.render_login_view()
        
        # Garante que campos de email e senha foram instanciados
        assert mock_input.call_count >= 2

def test_render_signup_view_structure():
    st.session_state.clear()
    with patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.markdown"), \
         patch("streamlit.form") as mock_form, \
         patch("streamlit.text_input") as mock_input, \
         patch("streamlit.form_submit_button", return_value=False), \
         patch("streamlit.button", return_value=False):
        
        mock_form.return_value.__enter__.return_value = None
        mock_form.return_value.__exit__.return_value = None
        
        auth_views.render_signup_view()
        
        # Garante que campos de nome, email e senhas foram chamados
        assert mock_input.call_count >= 3
