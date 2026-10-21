import streamlit as st
from typing import Callable, Optional
from src.core import auth_manager
from src.ui.navbar import set_page, clear_transient_state

def render_login_view(on_success_callback: Optional[Callable] = None):
    """
    Renderiza a tela dedicada de login centralizada no padrão SaaS.
    """
    # Container centralizado para foco e clareza
    _, col_center, _ = st.columns([1, 1.6, 1])

    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">🔐</div>
            <h2 style="margin: 0; font-weight: 700; color: #f8fafc;">Entrar no GitMatch</h2>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px;">
                Acesse suas candidaturas, seu perfil salvo e economize tokens com cache de projetos.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("auth_error"):
            st.error(f"⚠️ {st.session_state.auth_error}")

        with st.form("form_login_dedicated", clear_on_submit=False):
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", key="login_field_email")
            password = st.text_input("Senha", type="password", placeholder="Sua senha secreta", key="login_field_password")
            
            submit_btn = st.form_submit_button("Acessar Conta 🚀", type="primary", use_container_width=True)

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

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        col_alt1, col_alt2 = st.columns(2)
        with col_alt1:
            if st.button("✨ Não tem conta? Cadastre-se", key="btn_go_to_signup", use_container_width=True):
                set_page("signup")
                st.rerun()
        with col_alt2:
            if st.button("👤 Continuar como Convidado", key="btn_guest_from_login", use_container_width=True):
                st.session_state.user_session = auth_manager.create_guest_session()
                if on_success_callback:
                    on_success_callback()
                set_page("dashboard")
                st.rerun()

def render_signup_view(on_success_callback: Optional[Callable] = None):
    """
    Renderiza a tela dedicada de cadastro centralizada no padrão SaaS.
    """
    _, col_center, _ = st.columns([1, 1.6, 1])

    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">✨</div>
            <h2 style="margin: 0; font-weight: 700; color: #f8fafc;">Criar Conta no GitMatch</h2>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 6px;">
                Crie sua conta para sincronizar currículos e reaproveitar dados em nuvem via Supabase.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get("auth_error"):
            st.error(f"⚠️ {st.session_state.auth_error}")

        with st.form("form_signup_dedicated", clear_on_submit=False):
            name = st.text_input("Nome Completo", placeholder="Ex: Thiago Silva", key="signup_field_name")
            email = st.text_input("E-mail", placeholder="seu.email@exemplo.com", key="signup_field_email")
            password = st.text_input("Senha (mínimo 6 caracteres)", type="password", placeholder="••••••••", key="signup_field_pass")
            password_confirm = st.text_input("Confirme sua Senha", type="password", placeholder="••••••••", key="signup_field_pass_confirm")
            
            submit_btn = st.form_submit_button("Cadastrar e Começar 🎉", type="primary", use_container_width=True)

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

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        col_alt1, col_alt2 = st.columns(2)
        with col_alt1:
            if st.button("🔐 Já possui conta? Faça Login", key="btn_go_to_login", use_container_width=True):
                set_page("login")
                st.rerun()
        with col_alt2:
            if st.button("👤 Continuar como Convidado", key="btn_guest_from_signup", use_container_width=True):
                st.session_state.user_session = auth_manager.create_guest_session()
                if on_success_callback:
                    on_success_callback()
                set_page("dashboard")
                st.rerun()
