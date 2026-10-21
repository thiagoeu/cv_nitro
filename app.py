import os
import streamlit as st
from src.core import history_manager, auth_manager
from src.agents.graph import build_graph
from src.ui.navbar import render_navbar, set_page
from src.ui.components import apply_theme
from src.ui.dashboard_view import render_dashboard_view
from src.ui.wizard_view import render_wizard_view
from src.ui.applications_view import render_applications_view, render_applications_list as ui_render_apps_list
from src.ui.profile_view import render_profile_view
from src.ui.settings_view import render_settings_view
from src.ui.auth_views import render_login_view, render_signup_view, render_logout_view

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.svg")

# 1. Configuração da Página
st.set_page_config(
    page_title="GitMatch - CV Nitro Optimizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="auto"
)

# 2. Compilação do Grafo Multi-Agente
graph = build_graph()

# 3. Inicialização do Estado de Sessão
if "user_session" not in st.session_state:
    st.session_state.user_session = auth_manager.create_guest_session()
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# 4. Funções de Cache de Alta Performance
@st.cache_data(ttl=30, show_spinner=False)
def get_cached_resumes(user_id: str = "guest_local"):
    """Recupera lista de candidaturas com cache curto para resposta instantânea."""
    return history_manager.list_resumes(user_id=user_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_application(filepath: str):
    """Carrega dados da aplicação com cache em memória para visualização sem latência."""
    return history_manager.load_application(filepath)

def clear_history_cache():
    """Invalida o cache após salvar, atualizar ou excluir candidaturas."""
    get_cached_resumes.clear()
    get_cached_application.clear()

def render_sidebar(resumes: list = None):
    """Barra lateral de acesso rápido às candidaturas recentes (só para usuários conectados)."""
    session = st.session_state.get("user_session", auth_manager.create_guest_session())
    if session.get("is_guest", True):
        return

    st.sidebar.markdown("#### :material/history: Recentes")
    if resumes is None:
        resumes = get_cached_resumes(session.get("user_id", "guest_local"))

    if not resumes:
        st.sidebar.caption("Nenhuma candidatura ainda.")
        return

    for idx, r in enumerate(resumes[:8]):
        date_str = history_manager.format_display_date(r.get("date", ""))
        lang = (r.get("language") or "pt").upper()
        label = f"**{(r.get('job_title') or 'Vaga').strip()}**  \n:gray[{lang} · {date_str}]"
        if st.sidebar.button(label, key=f"sb_quick_{idx}", type="tertiary", width="stretch"):
            st.session_state.viewing_history = r["filepath"]
            set_page("applications", clear_transient=False)
            st.rerun()

# Wrappers de compatibilidade retroativa para testes e integrações externas
def render_dashboard(resumes: list):
    render_dashboard_view(resumes)

def render_settings():
    render_settings_view(clear_history_cache)

def render_applications_list(resumes: list):
    ui_render_apps_list(resumes)

def main():
    apply_theme()
    st.logo(LOGO_PATH, size="large")

    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    resumes = get_cached_resumes(current_uid)

    # Navbar superior com os links das páginas e o menu de conta
    page = render_navbar({
        "dashboard": lambda: render_dashboard_view(resumes),
        "wizard": lambda: render_wizard_view(graph, clear_history_cache),
        "applications": lambda: render_applications_view(resumes, get_cached_application, clear_history_cache, graph),
        "profile": render_profile_view,
        "settings": lambda: render_settings_view(clear_history_cache),
        "login": lambda: render_login_view(on_success_callback=clear_history_cache),
        "signup": lambda: render_signup_view(on_success_callback=clear_history_cache),
        "logout": lambda: render_logout_view(on_success_callback=clear_history_cache),
    })

    render_sidebar(resumes)
    page.run()

if __name__ == "__main__":
    main()
