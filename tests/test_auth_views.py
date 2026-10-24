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

def test_login_success_stores_auth_token():
    st.session_state.clear()
    st.query_params.clear()

    mock_user = {
        "user_id": "usr_abc",
        "email": "test@domain.com",
        "display_name": "Test User",
        "is_authenticated": True,
        "is_guest": False
    }

    with patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.markdown"), \
         patch("streamlit.form"), \
         patch("streamlit.text_input"), \
         patch("streamlit.form_submit_button", return_value=True), \
         patch("streamlit.button", return_value=False), \
         patch("streamlit.toast"), \
         patch("streamlit.rerun"), \
         patch("src.ui.auth_views.auth_manager.sign_in_with_password", return_value={"success": True, "user": mock_user}), \
         patch("src.ui.auth_views.set_page") as mock_set_page:
        
        # Simula preenchimento dos campos via monkeypatch do form submission
        auth_views.render_login_view()
        # Se campos forem vazios pelo mock de text_input, auth_error é disparado
        # Vamos testar chamando com campos preenchidos
    
    with patch("streamlit.columns", side_effect=mock_columns), \
         patch("streamlit.markdown"), \
         patch("streamlit.form"), \
         patch("streamlit.text_input", side_effect=["test@domain.com", "senha123"]), \
         patch("streamlit.form_submit_button", return_value=True), \
         patch("streamlit.button", return_value=False), \
         patch("streamlit.toast"), \
         patch("streamlit.rerun"), \
         patch("src.ui.auth_views.auth_manager.sign_in_with_password", return_value={"success": True, "user": mock_user}), \
         patch("src.ui.auth_views.set_page") as mock_set_page:
        
        auth_views.render_login_view()
        assert st.session_state.user_session["user_id"] == "usr_abc"
        assert "auth_token" not in st.query_params
        mock_set_page.assert_called_with("dashboard")
