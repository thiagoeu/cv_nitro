import streamlit as st
from typing import Dict, Any, Optional
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
    """
    if clear_transient:
        clear_transient_state()
    st.session_state.current_page = page_name
    # Se estiver navegando para fora da visualização de detalhe de candidatura, fecha-a
    if page_name != "applications" and "viewing_history" in st.session_state:
        del st.session_state["viewing_history"]

def get_current_page() -> str:
    """Retorna a página atualmente ativa (padrão: dashboard)."""
    return st.session_state.get("current_page", "dashboard")

def render_navbar() -> str:
    """
    Renderiza o cabeçalho superior no padrão SaaS com:
    - Logotipo da marca e badge
    - Abas de navegação horizontal (sem botões de rádio ou estilo de formulário)
    - Área de perfil/autenticação no canto superior direito
    """
    current_page = get_current_page()
    session = st.session_state.get("user_session", auth_manager.create_guest_session())
    is_guest = session.get("is_guest", True)
    user_name = session.get("display_name") or session.get("email") or "Candidato"

    # Injeção de CSS para estilização moderna e premium da Navbar
    st.markdown("""
    <style>
        .navbar-brand-container {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.25rem;
            font-weight: 700;
            color: #f8fafc;
            letter-spacing: -0.02em;
            padding: 4px 0;
        }
        .navbar-badge {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: white;
            font-size: 0.70rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .user-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: #94a3b8;
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        /* Remove espaçamento excessivo superior padrão do Streamlit */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Layout de colunas do Header: [Logo + Brand] | [Nav Tabs] | [Auth Area]
    col_brand, col_tabs, col_auth = st.columns([3.0, 5.2, 3.8], vertical_alignment="center")

    with col_brand:
        st.markdown(
            '<div class="navbar-brand-container">'
            '<span>🎯 GitMatch</span>'
            '<span class="navbar-badge">CV Nitro</span>'
            '</div>',
            unsafe_allow_html=True
        )

    with col_tabs:
        # Abas horizontais no formato SaaS
        t1, t2, t3, t4 = st.columns(4)
        
        with t1:
            is_active = (current_page == "dashboard")
            if st.button("📊 Dashboard", key="nav_btn_dash", type="primary" if is_active else "secondary", use_container_width=True):
                set_page("dashboard")
                st.rerun()

        with t2:
            is_active = (current_page == "wizard")
            if st.button("🚀 Otimizador", key="nav_btn_wiz", type="primary" if is_active else "secondary", use_container_width=True):
                set_page("wizard")
                st.rerun()

        with t3:
            is_active = (current_page == "applications")
            if st.button("📚 Vagas", key="nav_btn_apps", type="primary" if is_active else "secondary", use_container_width=True):
                set_page("applications")
                st.rerun()

        with t4:
            is_active = (current_page == "settings")
            if st.button("⚙️ Ajustes", key="nav_btn_sett", type="primary" if is_active else "secondary", use_container_width=True):
                set_page("settings")
                st.rerun()

    with col_auth:
        if is_guest:
            # Opções de Login e Cadastro para Convidado
            a1, a2 = st.columns(2)
            with a1:
                is_active = (current_page == "login")
                if st.button("🔑 Entrar", key="nav_btn_login", type="primary" if is_active else "secondary", use_container_width=True):
                    set_page("login")
                    st.rerun()
            with a2:
                is_active = (current_page == "signup")
                if st.button("✨ Criar Conta", key="nav_btn_signup", type="primary" if is_active else "secondary", use_container_width=True):
                    set_page("signup")
                    st.rerun()
        else:
            # Usuário autenticado
            u_col1, u_col2 = st.columns([2.2, 1.2], vertical_alignment="center")
            with u_col1:
                st.markdown(
                    f'<div class="user-status-pill">🟢 <b>{user_name[:12]}</b></div>',
                    unsafe_allow_html=True
                )
            with u_col2:
                if st.button("Sair", key="nav_btn_logout", type="secondary", use_container_width=True):
                    auth_manager.sign_out()
                    st.session_state.user_session = auth_manager.create_guest_session()
                    clear_transient_state()
                    set_page("dashboard")
                    st.toast("Sessão encerrada.")
                    st.rerun()

    st.markdown("<hr style='margin-top: 8px; margin-bottom: 20px; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)
    return current_page
