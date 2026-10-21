import streamlit as st
from typing import Callable, Dict
from src.core import auth_manager

# Chaves conhecidas de erros e alertas temporários para expurgo em clear_transient_state()
TRANSIENT_KEYS = [
    "transient_error",
    "transient_warning",
    "transient_info",
    "transient_success",
    "wizard_errors",
    "auth_error",
    "auth_success",
    "search_error",
    "last_error"
]

# chave interna -> (título, ícone, caminho na URL)
PAGES = {
    "dashboard": ("Dashboard", ":material/space_dashboard:", "dashboard"),
    "wizard": ("Otimizador", ":material/auto_awesome:", "otimizador"),
    "applications": ("Candidaturas", ":material/work_history:", "candidaturas"),
    "profile": ("Perfil", ":material/badge:", "perfil"),
    "login": ("Entrar", ":material/login:", "entrar"),
    "signup": ("Criar conta", ":material/person_add:", "cadastro"),
    "settings": ("Sistema", ":material/settings:", "sistema"),
    "logout": ("Sair", ":material/logout:", "sair"),
}
MAIN_LINKS = ["dashboard", "wizard", "applications", "profile"]
ACCOUNT_LINKS = ["login", "signup", "settings", "logout"]

def clear_transient_state():
    """
    Limpa mensagens de erro, alertas e estados transitórios do st.session_state
    antes de novas buscas, otimizações ou transições de tela.
    """
    for key in TRANSIENT_KEYS:
        if key in st.session_state:
            st.session_state[key] = None

def set_page(page_name: str, clear_transient: bool = True):
    """
    Define a página atual e opcionalmente limpa o estado de erro transitório.
    A troca efetiva acontece no próximo st.rerun(), dentro de render_navbar().
    """
    if clear_transient:
        clear_transient_state()
    st.session_state.current_page = page_name
    st.session_state["_nav_target"] = page_name
    # Se estiver navegando para fora da visualização de detalhe de candidatura, fecha-a
    if page_name != "applications" and "viewing_history" in st.session_state:
        del st.session_state["viewing_history"]

def get_current_page() -> str:
    """Retorna a página atualmente ativa (padrão: dashboard)."""
    return st.session_state.get("current_page", "dashboard")

def render_navbar(views: Dict[str, Callable[[], None]]):
    """
    Navbar superior nativa (st.navigation no topo): links das páginas principais
    e um menu de conta em dropdown. Retorna a página atual; chame .run() nela.
    """
    session = st.session_state.get("user_session", auth_manager.create_guest_session())
    is_guest = session.get("is_guest", True)
    # Todas as páginas ficam registradas; só a visibilidade muda com o login,
    # assim a navegação nunca cai numa página "inexistente" ao entrar/sair.
    hidden = {"logout"} if is_guest else {"login", "signup"}

    pages = {
        key: st.Page(
            views[key],
            title=title,
            icon=icon,
            url_path=url_path,
            default=(key == "dashboard"),
            visibility="hidden" if key in hidden else "visible"
        )
        for key, (title, icon, url_path) in PAGES.items()
    }

    if is_guest:
        account_label = "Conta"
    else:
        name = session.get("display_name") or session.get("email") or "Minha conta"
        account_label = f":material/account_circle: {name[:20]}"

    current = st.navigation(
        {"": [pages[k] for k in MAIN_LINKS], account_label: [pages[k] for k in ACCOUNT_LINKS]},
        position="top"
    )

    # Navegação programática pendente (set_page + st.rerun em qualquer view)
    target = st.session_state.pop("_nav_target", None)
    if target in pages and pages[target] is not current:
        st.switch_page(pages[target])

    st.session_state.current_page = next((k for k, p in pages.items() if p is current), "dashboard")
    return current
