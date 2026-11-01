import os
import urllib.parse
import streamlit as st
from src.core import history_manager, auth_manager, config
from src.agents.graph import build_graph
from src.ui.navbar import render_navbar, set_page
from src.ui.components import apply_theme, render_footer, render_storage_sync, SESSION_COOKIE
from src.ui.dashboard_view import render_dashboard_view
from src.ui.wizard_view import render_wizard_view
from src.ui.applications_view import render_applications_view
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

if not config.AUTH_SECRET_KEY:
    st.error(
        "**AUTH_SECRET_KEY não configurada.** Gere uma chave com "
        "`python -c \"import secrets; print(secrets.token_urlsafe(48))\"`, "
        "defina `AUTH_SECRET_KEY` no `.env` e reinicie o app.",
        icon=":material/key_off:"
    )
    st.stop()

# 2. Grafo Multi-Agente compilado uma vez por processo
@st.cache_resource(show_spinner=False)
def get_graph():
    return build_graph()

graph = get_graph()

# 3. Restauração de sessão pelo cookie assinado (F5); token na URL nunca é considerado
def restore_session():
    if st.session_state.get("logged_out"):
        # st.context.cookies é o retrato da requisição inicial: o cookie expirado no logout
        # continua aparecendo até a página ser recarregada, então só um novo login limpa a flag.
        st.session_state.user_session = auth_manager.create_guest_session()
    elif "user_session" not in st.session_state or st.session_state.user_session.get("is_guest", True):
        try:
            raw_cookie_token = st.context.cookies.get(SESSION_COOKIE)
        except Exception:
            raw_cookie_token = None
        restored_user = None
        if raw_cookie_token:
            restored_user = auth_manager.restore_session_from_token(urllib.parse.unquote(str(raw_cookie_token).strip('"')))
        st.session_state.user_session = restored_user or auth_manager.create_guest_session()

restore_session()

session = st.session_state.get("user_session", {})
is_guest = session.get("is_guest", True)

# Token renovado a cada execução (expiração deslizante de 30 dias)
active_token = None if is_guest else auth_manager.create_session_token(session)

if "current_page" not in st.session_state:
    st.session_state.current_page = "landing" if is_guest else "dashboard"

# 4. Funções de Cache de Alta Performance
@st.cache_data(ttl=30, show_spinner=False)
def get_cached_resumes(user_id: str = "guest_local"):
    """Recupera lista de candidaturas com cache curto para resposta instantânea."""
    return history_manager.list_resumes(user_id=user_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_application(filepath: str, user_id: str):
    """Carrega dados da aplicação com cache em memória para visualização sem latência."""
    return history_manager.load_application(filepath, user_id)

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

def main():
    apply_theme()
    st.logo(LOGO_PATH, size="large")

    # Grava (login) ou expira (logout) o cookie de sessão no navegador
    render_storage_sync(token=active_token, is_logout=st.session_state.get("logged_out", False))

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
