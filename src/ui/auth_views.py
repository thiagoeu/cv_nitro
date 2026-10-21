import streamlit as st
from typing import Callable, Optional
from src.core import auth_manager
from src.ui.navbar import set_page, clear_transient_state

def _auth_header(title: str, subtitle: str):
    """Título centralizado dos cartões de autenticação."""
    st.markdown(f"### {title}", text_alignment="center", anchors=False)
    st.caption(subtitle, text_alignment="center")

def _continue_as_guest(on_success_callback: Optional[Callable], key: str):
    if st.button("Continuar como visitante", type="tertiary", icon=":material/person:", key=key):
        st.session_state.user_session = auth_manager.create_guest_session()
        if on_success_callback:
            on_success_callback()
        set_page("dashboard")
        st.rerun()

def render_login_view(on_success_callback: Optional[Callable] = None):
    """
    Renderiza a tela dedicada de login centralizada no padrão SaaS.
    """
    _, col_center, _ = st.columns([1, 1.3, 1])

    with col_center:
        st.space("medium")
        _auth_header("Entrar no GitMatch", "Acesse suas candidaturas, seu perfil salvo e o cache de projetos.")

        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error, icon=":material/error:")

        with st.form("form_login_dedicated", clear_on_submit=False):
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", icon=":material/mail:", key="login_field_email")
            password = st.text_input("Senha", type="password", placeholder="Sua senha", icon=":material/lock:", key="login_field_password")
            submit_btn = st.form_submit_button("Entrar", type="primary", icon=":material/login:", width="stretch")

        if submit_btn:
            clear_transient_state()
            if not email or not password:
                st.session_state.auth_error = "Por favor, preencha o e-mail e a senha."
                st.rerun()
            else:
                res = auth_manager.sign_in_with_password(email.strip(), password)
                if res["success"]:
                    st.session_state.user_session = res["user"]
                    if on_success_callback:
                        on_success_callback()
                    st.toast(f"Bem-vindo(a) de volta, {res['user']['display_name']}!")
                    set_page("dashboard")
                    st.rerun()
                else:
                    st.session_state.auth_error = res.get("error", "Falha ao autenticar.")
                    st.rerun()

        with st.container(horizontal=True, horizontal_alignment="center"):
            if st.button("Não tem conta? Cadastre-se", type="tertiary", icon=":material/person_add:", key="btn_go_to_signup"):
                set_page("signup")
                st.rerun()
            _continue_as_guest(on_success_callback, key="btn_guest_from_login")

def render_signup_view(on_success_callback: Optional[Callable] = None):
    """
    Renderiza a tela dedicada de cadastro centralizada no padrão SaaS.
    """
    _, col_center, _ = st.columns([1, 1.3, 1])

    with col_center:
        st.space("medium")
        _auth_header("Criar conta no GitMatch", "Sincronize currículos e reaproveite seu perfil em qualquer otimização.")

        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error, icon=":material/error:")

        with st.form("form_signup_dedicated", clear_on_submit=False):
            name = st.text_input("Nome completo", placeholder="Ex: Thiago Silva", icon=":material/person:", key="signup_field_name")
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", icon=":material/mail:", key="signup_field_email")
            col_pass, col_confirm = st.columns(2)
            with col_pass:
                password = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="signup_field_pass")
            with col_confirm:
                password_confirm = st.text_input("Confirme a senha", type="password", placeholder="Repita a senha", key="signup_field_pass_confirm")
            submit_btn = st.form_submit_button("Criar conta", type="primary", icon=":material/rocket_launch:", width="stretch")

        if submit_btn:
            clear_transient_state()
            if not email or not password:
                st.session_state.auth_error = "Por favor, preencha todos os campos obrigatórios."
                st.rerun()
            elif len(password) < 6:
                st.session_state.auth_error = "A senha deve conter pelo menos 6 caracteres."
                st.rerun()
            elif password != password_confirm:
                st.session_state.auth_error = "As senhas não coincidem. Digite novamente."
                st.rerun()
            else:
                res = auth_manager.sign_up(email.strip(), password, full_name=name.strip())
                if res["success"]:
                    st.session_state.user_session = res["user"]
                    if on_success_callback:
                        on_success_callback()
                    st.toast(res.get("message", "Conta criada com sucesso!"))
                    set_page("dashboard")
                    st.rerun()
                else:
                    st.session_state.auth_error = res.get("error", "Falha ao registrar conta.")
                    st.rerun()

        with st.container(horizontal=True, horizontal_alignment="center"):
            if st.button("Já tem conta? Entrar", type="tertiary", icon=":material/login:", key="btn_go_to_login"):
                set_page("login")
                st.rerun()
            _continue_as_guest(on_success_callback, key="btn_guest_from_signup")

def render_logout_view(on_success_callback: Optional[Callable] = None):
    """Página 'Sair' do menu de conta: encerra a sessão e volta ao dashboard."""
    auth_manager.sign_out()
    st.session_state.user_session = auth_manager.create_guest_session()
    clear_transient_state()
    if on_success_callback:
        on_success_callback()
    st.toast("Sessão encerrada.", icon=":material/logout:")
    set_page("dashboard")
    st.rerun()
