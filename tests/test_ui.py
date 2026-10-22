import streamlit as st
from src.ui.diagnostic_view import render_ats_diagnostic_panel
from unittest.mock import patch, MagicMock

def test_diagnostic_panel_with_data():
    sample_diagnostic = {
        "ats_score": 92,
        "matched_keywords": ["Python", "FastAPI", "Docker"],
        "applied_changes": ["Formatação em Markdown ATS", "Habilidades em 2 colunas"],
        "reviewer_summary": "Currículo atende plenamente aos requisitos da vaga."
    }
    
    def fake_columns(spec):
        count = len(spec) if isinstance(spec, list) else spec
        return [MagicMock() for _ in range(count)]

    with patch("streamlit.metric") as mock_metric, \
         patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.info") as mock_info, \
         patch("streamlit.columns", side_effect=fake_columns):
        render_ats_diagnostic_panel(sample_diagnostic)
        assert mock_metric.called
        assert mock_info.called

def test_diagnostic_panel_with_empty_data():
    with patch("streamlit.info") as mock_info:
        render_ats_diagnostic_panel({})
        assert mock_info.called

def test_theme_tokens_and_apply_theme():
    from src.ui.components import THEME_TOKENS, apply_theme
    assert THEME_TOKENS["bg_neutral"] == "#F8FAFC"
    assert THEME_TOKENS["bg_surface"] == "#F1F5F9"
    assert THEME_TOKENS["text_primary"] == "#0F172A"
    assert THEME_TOKENS["border"] == "#CBD5E1"
    assert THEME_TOKENS["accent_mint"] == "#10B981"
    assert THEME_TOKENS["accent_cyan"] == "#0EA5E9"

    with patch("streamlit.markdown") as mock_markdown:
        apply_theme()
        assert mock_markdown.called
        css_injected = mock_markdown.call_args[0][0]
        assert "#CBD5E1" in css_injected
        assert "#10B981" in css_injected
        assert "@media print" in css_injected
        assert "app-global-footer-wrapper" in css_injected

def test_render_landing_view():
    from src.ui.landing_view import render_landing_view

    def fake_columns(spec):
        count = len(spec) if isinstance(spec, list) else spec
        return [MagicMock() for _ in range(count)]

    with patch("streamlit.markdown") as mock_markdown, \
         patch("streamlit.columns", side_effect=fake_columns), \
         patch("streamlit.button", return_value=False) as mock_button:
        render_landing_view()
        assert mock_markdown.called
        # Verificar se os títulos e textos de impacto foram enviados para st.markdown
        all_markdown_texts = " ".join([call[0][0] for call in mock_markdown.call_args_list if call[0]])
        assert "Com o CV-Nitro, você se destaca em qualquer processo seletivo tech" in all_markdown_texts
        assert "Análise Profunda da Vaga" in all_markdown_texts
        # Garantir que a caixa escura e botões de baixo foram removidos
        assert "Pronto para conquistar sua próxima vaga tech?" not in all_markdown_texts
        assert mock_button.called

def test_render_footer():
    from src.ui.components import render_footer

    with patch("streamlit.markdown") as mock_markdown:
        render_footer()
        assert mock_markdown.called
        footer_html = mock_markdown.call_args[0][0]
        assert "Thiago Araújo" in footer_html
        assert "araujo.thiago1051@gmail.com" in footer_html
        assert "github.com/thiagoeu" in footer_html
        assert "Sistemas Multi-Agentes (SMA)" in footer_html
        assert "Licença MIT" in footer_html
        assert "app-global-footer" in footer_html
        assert "app-global-footer-wrapper" in footer_html

def test_landing_page_cta_interactions():
    from src.ui.landing_view import render_landing_view

    def fake_columns(spec):
        count = len(spec) if isinstance(spec, list) else spec
        return [MagicMock() for _ in range(count)]

    # Cenário: Usuário clica no botão de signup da hero
    def button_signup_click(label, **kwargs):
        return kwargs.get("key") == "landing_btn_signup"

    with patch("streamlit.markdown"), \
         patch("streamlit.columns", side_effect=fake_columns), \
         patch("streamlit.button", side_effect=button_signup_click), \
         patch("src.ui.landing_view.set_page") as mock_set_page, \
         patch("streamlit.rerun") as mock_rerun:
        render_landing_view()
        mock_set_page.assert_called_with("signup")
        assert mock_rerun.called

def test_navbar_guest_route_protection_and_navigation():
    import streamlit as st
    from src.ui.navbar import render_navbar

    st.session_state.clear()
    st.session_state.user_session = {"is_guest": True, "user_id": "guest_local"}
    st.session_state.current_page = "dashboard"  # Tentativa de acesso a rota privada

    views = {
        "landing": MagicMock(),
        "dashboard": MagicMock(),
        "wizard": MagicMock(),
        "applications": MagicMock(),
        "profile": MagicMock(),
        "settings": MagicMock(),
        "login": MagicMock(),
        "signup": MagicMock(),
        "logout": MagicMock(),
    }

    mock_page_instances = {}
    def fake_page(func, **kwargs):
        p = MagicMock()
        p.title = kwargs.get("title")
        p.url_path = kwargs.get("url_path")
        return p

    with patch("streamlit.Page", side_effect=fake_page), \
         patch("streamlit.navigation") as mock_navigation:
        mock_navigation.return_value = MagicMock()
        render_navbar(views)
        
        # Rota privada deve ter sido interceptada e alterada para landing
        assert st.session_state.current_page == "landing"
        assert st.session_state.get("transient_info") is not None
        
        # st.navigation deve ter sido chamado apenas com seções públicas
        nav_call_args = mock_navigation.call_args[0][0]
        assert "" in nav_call_args
        assert "Conta" in nav_call_args
        # Deve ter 1 link no principal (landing) e 2 em conta (login e signup)
        assert len(nav_call_args[""]) == 1
        assert len(nav_call_args["Conta"]) == 2

def test_navbar_authenticated_user_navigation():
    import streamlit as st
    from src.ui.navbar import render_navbar

    st.session_state.clear()
    st.session_state.user_session = {"is_guest": False, "user_id": "u-123", "display_name": "Dev Nitro"}
    st.session_state.current_page = "dashboard"

    views = {
        "landing": MagicMock(),
        "dashboard": MagicMock(),
        "wizard": MagicMock(),
        "applications": MagicMock(),
        "profile": MagicMock(),
        "settings": MagicMock(),
        "login": MagicMock(),
        "signup": MagicMock(),
        "logout": MagicMock(),
    }

    def fake_page(func, **kwargs):
        p = MagicMock()
        p.title = kwargs.get("title")
        return p

    with patch("streamlit.Page", side_effect=fake_page), \
         patch("streamlit.navigation") as mock_navigation:
        mock_navigation.return_value = MagicMock()
        render_navbar(views)

        assert st.session_state.current_page == "dashboard"
        nav_call_args = mock_navigation.call_args[0][0]
        # Deve ter os 4 links principais
        assert len(nav_call_args[""]) == 4
        # E o menu de conta autenticada
        account_section = [k for k in nav_call_args.keys() if "Dev Nitro" in k][0]
        assert len(nav_call_args[account_section]) == 2  # settings e logout

def test_auth_logout_redirects_to_landing():
    from src.ui.auth_views import render_logout_view

    st.query_params.clear()
    st.query_params["auth_token"] = "some-token"
    with patch("src.ui.auth_views.auth_manager.sign_out") as mock_sign_out, \
         patch("src.ui.auth_views.set_page") as mock_set_page, \
         patch("streamlit.toast"), \
         patch("streamlit.rerun"):
        render_logout_view()
        assert mock_sign_out.called
        assert st.session_state.user_session["is_guest"] is True
        assert st.query_params.get("action") == "logout"
        assert "auth_token" not in st.query_params
        mock_set_page.assert_called_with("landing")

def test_render_storage_sync_authenticated():
    from src.ui.components import render_storage_sync

    with patch("streamlit.components.v1.html") as mock_html:
        render_storage_sync(token="valid.test.token", is_logout=False)
        assert mock_html.called
        script_arg = mock_html.call_args[0][0]
        assert "valid.test.token" in script_arg
        assert "cv_nitro_auth_token" in script_arg
        assert "isLogout = false" in script_arg

def test_render_storage_sync_logout():
    from src.ui.components import render_storage_sync

    with patch("streamlit.components.v1.html") as mock_html:
        render_storage_sync(token=None, is_logout=True)
        assert mock_html.called
        script_arg = mock_html.call_args[0][0]
        assert "removeItem(storageKey)" in script_arg
        assert "isLogout = true" in script_arg

