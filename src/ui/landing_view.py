import streamlit as st
from src.ui.navbar import set_page
from src.ui.components import THEME_TOKENS

def render_landing_view():
    """
    Landing Page pública institucional do CV-Nitro para visitantes não autenticados.
    Apresenta a proposta de valor, pilares da IA multi-agente e botões de ação para login/cadastro.
    """
    # 1. Hero Section
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2.5rem 1rem 1.5rem 1rem; max-width: 900px; margin: 0 auto;">
            <div style="display: inline-flex; align-items: center; gap: 8px; background: {THEME_TOKENS['bg_surface']}; border: 1px solid {THEME_TOKENS['border']}; color: {THEME_TOKENS['accent_cyan']}; padding: 6px 16px; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; margin-bottom: 1.25rem;">
                ⚡ Otimizador de Carreira com Inteligência Artificial Multi-Agente
            </div>
            <h1 style="color: {THEME_TOKENS['text_primary']}; font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 1.25rem; letter-spacing: -0.02em;">
                Com o CV-Nitro, você se destaca em qualquer processo seletivo tech
            </h1>
            <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 1.18rem; line-height: 1.6; max-width: 760px; margin: 0 auto 2rem auto;">
                Pare de enviar currículos genéricos. O CV-Nitro analisa os requisitos da vaga com agentes de IA,
                alinha suas experiências reais aos filtros de ATS e gera cartas de apresentação persuasivas em segundos.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Botões de Ação Principais (CTAs)
    cta_col_left, cta_col_1, cta_col_2, cta_col_right = st.columns([1.5, 2.2, 2.2, 1.5])
    with cta_col_1:
        if st.button("🚀 Criar Conta Grátis", type="primary", key="landing_btn_signup", use_container_width=True):
            set_page("signup")
            st.rerun()

    with cta_col_2:
        if st.button("🔑 Já tenho conta / Entrar", type="secondary", key="landing_btn_login", use_container_width=True):
            set_page("login")
            st.rerun()

    st.markdown("<div style='margin-bottom: 3.5rem;'></div>", unsafe_allow_html=True)

    # 2. Pilares de Valor (Grid 4 Cards)
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <span style="color: {THEME_TOKENS['accent_mint']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.85rem;">Diferenciais Exclusivos</span>
            <h2 style="color: {THEME_TOKENS['text_primary']}; font-size: 1.8rem; font-weight: 700; margin-top: 0.3rem;">Por que o CV-Nitro acelera suas contratações?</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    card_style = f"""
        background-color: {THEME_TOKENS['bg_card']};
        border: 1px solid {THEME_TOKENS['border']};
        border-radius: {THEME_TOKENS['radius']};
        padding: 1.4rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04);
    """

    with col1:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1.8rem; margin-bottom: 0.75rem;">🔍</div>
                <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.5rem; font-size: 1.05rem;">Análise Profunda da Vaga</h4>
                <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Nossos agentes de IA decompõem a job description identificando hard skills, soft skills e requisitos chave da empresa.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1.8rem; margin-bottom: 0.75rem;">🎯</div>
                <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.5rem; font-size: 1.05rem;">Alinhamento ATS Preciso</h4>
                <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Reescrevemos seus impactos reais usando a taxonomia exata dos robôs de triagem sem inventar dados falsos.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1.8rem; margin-bottom: 0.75rem;">📊</div>
                <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.5rem; font-size: 1.05rem;">Diagnóstico e Score</h4>
                <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Receba pontuação instantânea de aderência de 0 a 100, lista de lacunas identificadas e recomendações de melhoria.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="font-size: 1.8rem; margin-bottom: 0.75rem;">✉️</div>
                <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.5rem; font-size: 1.05rem;">Carta Sob Medida</h4>
                <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                    Gere cartas de apresentação altamente personalizadas que conectam sua trajetória aos desafios da vaga.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 3.5rem;'></div>", unsafe_allow_html=True)

    # 3. Como Funciona (3 Passos)
    st.markdown(
        f"""
        <div style="background-color: {THEME_TOKENS['bg_surface']}; border: 1px solid {THEME_TOKENS['border']}; border-radius: {THEME_TOKENS['radius']}; padding: 2.2rem 1.8rem; margin-bottom: 1.5rem;">
            <div style="text-align: center; margin-bottom: 2rem;">
                <span style="color: {THEME_TOKENS['accent_cyan']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.85rem;">Fluxo Descomplicado</span>
                <h2 style="color: {THEME_TOKENS['text_primary']}; font-size: 1.8rem; font-weight: 700; margin-top: 0.3rem;">Como o CV-Nitro funciona</h2>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem;">
                <div style="background: {THEME_TOKENS['bg_card']}; padding: 1.25rem; border-radius: 0.5rem; border: 1px solid {THEME_TOKENS['border']};">
                    <div style="color: {THEME_TOKENS['accent_mint']}; font-weight: 800; font-size: 1.4rem; margin-bottom: 0.5rem;">01</div>
                    <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.4rem;">Crie sua Conta</h4>
                    <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                        Cadastre-se gratuitamente em segundos e mantenha seu currículo base e perfil GitHub salvos com segurança.
                    </p>
                </div>
                <div style="background: {THEME_TOKENS['bg_card']}; padding: 1.25rem; border-radius: 0.5rem; border: 1px solid {THEME_TOKENS['border']};">
                    <div style="color: {THEME_TOKENS['accent_mint']}; font-weight: 800; font-size: 1.4rem; margin-bottom: 0.5rem;">02</div>
                    <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.4rem;">Cole a Descrição da Vaga</h4>
                    <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                        Basta colar o texto ou link da vaga desejada. Nosso sistema multi-agente orquestra a análise automática.
                    </p>
                </div>
                <div style="background: {THEME_TOKENS['bg_card']}; padding: 1.25rem; border-radius: 0.5rem; border: 1px solid {THEME_TOKENS['border']};">
                    <div style="color: {THEME_TOKENS['accent_mint']}; font-weight: 800; font-size: 1.4rem; margin-bottom: 0.5rem;">03</div>
                    <h4 style="color: {THEME_TOKENS['text_primary']}; font-weight: 700; margin-bottom: 0.4rem;">Receba seu CV Pronto</h4>
                    <p style="color: {THEME_TOKENS['text_secondary']}; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                        Obtenha seu currículo otimizado, diagnóstico ATS completo e carta personalizada prontos para download.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
