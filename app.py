import os
import streamlit as st
from src.core import history_manager, auth_manager
from src.agents.graph import build_graph
from src.ui.navbar import render_navbar, set_page
from src.ui.components import apply_theme, render_footer, render_storage_sync
from src.ui.dashboard_view import render_dashboard_view
from src.ui.wizard_view import render_wizard_view
from src.ui.applications_view import render_applications_view, render_applications_list as ui_render_apps_list
from src.ui.profile_view import render_profile_view
from src.ui.settings_view import render_settings_view
from src.ui.auth_views import render_login_view, render_signup_view, render_logout_view
from src.ui.landing_view import render_landing_view

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

# 3. Inicialização e Restauração de Sessão Persistente (F5 / LocalStorage)
action = st.query_params.get("action")
auth_token = st.query_params.get("auth_token")
is_logout_event = (action == "logout") or st.session_state.get("logged_out", False)

if is_logout_event:
    # Ação explícita de encerramento de sessão
    st.session_state.user_session = auth_manager.create_guest_session()
    st.session_state.current_page = "landing"
    st.query_params.pop("action", None)
    st.query_params.pop("auth_token", None)
else:
    # Se a sessão estiver vazia (ex: F5) ou como convidado, tenta restaurar token válido do handshake
    if "user_session" not in st.session_state or st.session_state.user_session.get("is_guest", True):
        if auth_token:
            restored_user = auth_manager.restore_session_from_token(auth_token)
            if restored_user:
                st.session_state.user_session = restored_user
            else:
                st.session_state.user_session = auth_manager.create_guest_session()
            # Remove o token da URL imediatamente para nunca ficar exposto ao usuário
            st.query_params.pop("auth_token", None)
        else:
            st.session_state.user_session = auth_manager.create_guest_session()

session = st.session_state.get("user_session", {})
is_guest = session.get("is_guest", True)

# Token assinado obtido da sessão para manter o localStorage sincronizado sem expor na URL
active_token = None
if not is_guest and session.get("is_authenticated", False):
    active_token = auth_manager.create_session_token(session)

if "current_page" not in st.session_state:
    st.session_state.current_page = "landing" if is_guest else "dashboard"

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

    # Sincronização em segundo plano com o localStorage e cookie do navegador
    curr_session = st.session_state.get("user_session", {})
    curr_guest = curr_session.get("is_guest", True)
    curr_token = active_token if not curr_guest else None
    render_storage_sync(token=curr_token, is_logout=is_logout_event)

    if is_logout_event:
        st.session_state.pop("logged_out", None)
        st.query_params.clear()

    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    resumes = get_cached_resumes(current_uid)

    # Navbar superior com os links das páginas e o menu de conta
    page = render_navbar({
        "landing": render_landing_view,
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
    render_footer()

if __name__ == "__main__":
    main()
