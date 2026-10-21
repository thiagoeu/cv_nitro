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

# Catálogo completo de páginas: chave interna -> (título, ícone, caminho na URL)
PAGES = {
    "landing": ("Início", ":material/home:", "inicio"),
    "dashboard": ("Dashboard", ":material/space_dashboard:", "dashboard"),
    "wizard": ("Otimizador", ":material/auto_awesome:", "otimizador"),
    "applications": ("Candidaturas", ":material/work_history:", "candidaturas"),
    "profile": ("Perfil", ":material/badge:", "perfil"),
    "login": ("Entrar", ":material/login:", "entrar"),
    "signup": ("Criar conta", ":material/person_add:", "cadastro"),
    "settings": ("Sistema", ":material/settings:", "sistema"),
    "logout": ("Sair", ":material/logout:", "sair"),
}

PUBLIC_PAGES = {"landing", "login", "signup"}
PRIVATE_PAGES = {"dashboard", "wizard", "applications", "profile", "settings", "logout"}

# Grupos de links para visitantes não autenticados
GUEST_MAIN_LINKS = ["landing"]
GUEST_ACCOUNT_LINKS = ["login", "signup"]

# Grupos de links para usuários autenticados
AUTH_MAIN_LINKS = ["dashboard", "wizard", "applications", "profile"]
AUTH_ACCOUNT_LINKS = ["settings", "logout"]

# Aliases de compatibilidade retroativa
MAIN_LINKS = AUTH_MAIN_LINKS
ACCOUNT_LINKS = AUTH_ACCOUNT_LINKS

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
    """Retorna a página atualmente ativa."""
    if "current_page" in st.session_state:
        return st.session_state.current_page
    session = st.session_state.get("user_session")
    if session and session.get("is_guest", True):
        return "landing"
    elif session and not session.get("is_guest", True):
        return "dashboard"
    return "dashboard"

def render_navbar(views: Dict[str, Callable[[], None]]):
    """
    Navbar superior nativa (st.navigation no topo):
    - Se visitante (is_guest == True): exibe apenas 'Início' e menu 'Conta' com 'Entrar' e 'Criar conta'.
      Protege todas as rotas privadas, redirecionando para 'landing'.
    - Se autenticado (is_guest == False): exibe as páginas da aplicação ('Dashboard', 'Otimizador', etc.)
      e menu de conta com perfil/configurações e logout.
    """
    session = st.session_state.get("user_session", auth_manager.create_guest_session())
    is_guest = session.get("is_guest", True)
    default_key = "landing" if is_guest else "dashboard"

    # Guarda de rotas: intercepta tentativas de acesso indevido
    current_requested = st.session_state.get("current_page", default_key)
    if is_guest and current_requested in PRIVATE_PAGES:
        st.session_state["transient_info"] = "Acesso restrito. Faça login ou crie sua conta para acessar o sistema."
        st.session_state.current_page = "landing"
        st.session_state.pop("_nav_target", None)
        default_key = "landing"
    elif not is_guest and current_requested == "landing":
        st.session_state.current_page = "dashboard"
        st.session_state.pop("_nav_target", None)
        default_key = "dashboard"

    if is_guest:
        # Visitante: apenas Landing Page e ações de Login/Cadastro
        allowed_keys = GUEST_MAIN_LINKS + GUEST_ACCOUNT_LINKS
        pages = {
            key: st.Page(
                views[key],
                title=title,
                icon=icon,
                url_path=url_path,
                default=(key == default_key)
            )
            for key, (title, icon, url_path) in PAGES.items()
            if key in allowed_keys and key in views
        }
        nav_sections = {
            "": [pages[k] for k in GUEST_MAIN_LINKS if k in pages],
            "Conta": [pages[k] for k in GUEST_ACCOUNT_LINKS if k in pages]
        }
    else:
        # Usuário autenticado: ferramentas da aplicação e menu de conta
        allowed_keys = AUTH_MAIN_LINKS + AUTH_ACCOUNT_LINKS
        pages = {
            key: st.Page(
                views[key],
                title=title,
                icon=icon,
                url_path=url_path,
                default=(key == default_key)
            )
            for key, (title, icon, url_path) in PAGES.items()
            if key in allowed_keys and key in views
        }
        name = session.get("display_name") or session.get("email") or "Minha conta"
        account_label = f":material/account_circle: {name[:20]}"
        nav_sections = {
            "": [pages[k] for k in AUTH_MAIN_LINKS if k in pages],
            account_label: [pages[k] for k in AUTH_ACCOUNT_LINKS if k in pages]
        }

    current = st.navigation(nav_sections, position="top")

    # Navegação programática pendente (set_page + st.rerun em qualquer view)
    target = st.session_state.pop("_nav_target", None)
    if target in pages and pages[target] is not current:
        st.switch_page(pages[target])

    st.session_state.current_page = next((k for k, p in pages.items() if p is current), default_key)
    return current
