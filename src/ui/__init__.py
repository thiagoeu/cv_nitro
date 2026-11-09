"""Camada de interface de usuário (Streamlit) do CV Nitro."""
from src.ui.navbar import render_navbar, set_page, clear_transient_state
from src.ui.components import (
    apply_theme,
    render_footer,
    render_storage_sync,
    page_header,
    login_gate,
    application_card,
    resume_input,
    notify_saved,
    SESSION_COOKIE,
)
from src.ui.theme import THEME_TOKENS
from src.ui.landing_view import render_landing_view
from src.ui.dashboard_view import render_dashboard_view
from src.ui.wizard_view import render_wizard_view
from src.ui.applications_view import render_applications_view, render_application_view
from src.ui.profile_view import render_profile_view
from src.ui.settings_view import render_settings_view
from src.ui.auth_views import render_login_view, render_signup_view, render_logout_view

__all__ = [
    # Navegação & Tema
    "render_navbar",
    "set_page",
    "clear_transient_state",
    "apply_theme",
    "render_footer",
    "render_storage_sync",
    "page_header",
    "login_gate",
    "application_card",
    "resume_input",
    "notify_saved",
    "SESSION_COOKIE",
    "THEME_TOKENS",
    # Views principais
    "render_landing_view",
    "render_dashboard_view",
    "render_wizard_view",
    "render_applications_view",
    "render_application_view",
    "render_profile_view",
    "render_settings_view",
    "render_login_view",
    "render_signup_view",
    "render_logout_view",
]
