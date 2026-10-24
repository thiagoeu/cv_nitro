import streamlit as st
from typing import Optional
from src.core import history_manager
from src.core.document_parser import extract_text_from_file
from src.ui.navbar import set_page

# Dicionário de Tokens da Paleta Clássico Tech Confiável (Regra 60-30-10)
THEME_TOKENS = {
    # 60% — Fundo neutro e áreas de leitura
    "bg_neutral": "#F8FAFC",      # Branco gelo
    "bg_surface": "#F1F5F9",      # Cinza claro para superfícies secundárias
    "bg_card": "#FFFFFF",         # Superfície branca pura para relevo de cards
    # 30% — Estrutura e identidade visual
    "text_primary": "#0F172A",    # Azul noturno (títulos, textos principais)
    "text_secondary": "#475569",  # Ardósia para subtítulos e captions
    "border": "#CBD5E1",          # Cinza azulado para divisórias e bordas
    "border_focus": "#0EA5E9",    # Ciano para borda de foco
    # 10% — Destaques e ações principais (CTAs)
    "accent_mint": "#10B981",     # Verde-menta (botões primários, sucesso)
    "accent_mint_hover": "#059669",
    "accent_cyan": "#0EA5E9",     # Ciano complementar (links, métricas tech, badges)
    "radius": "0.6rem",
}

# CSS global complementar ao .streamlit/config.toml
_CSS = f"""
<style>
    /* Remove elementos decorativos nativos do Streamlit desnecessários */
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"],
    #MainMenu,
    [data-testid="stDecoration"],
    footer {{
        display: none !important;
    }}

    /* Barra superior (Navbar): Fundo claro sólido #FFFFFF integrado com borda inferior #CBD5E1 */
    header[data-testid="stHeader"],
    .stAppHeader {{
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        border-bottom: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05) !important;
    }}

    /* Links e botões da barra superior */
    [data-testid="stTopNavLink"],
    [data-testid="stTopNavSection"] {{
        color: #475569 !important;
        font-weight: 500 !important;
        border-radius: 0.5rem !important;
        transition: color 0.15s ease, background-color 0.15s ease !important;
    }}

    [data-testid="stTopNavLink"] span,
    [data-testid="stTopNavSection"] span,
    [data-testid="stTopNavLink"] p,
    [data-testid="stTopNavSection"] p {{
        color: #475569 !important;
    }}

    [data-testid="stTopNavLink"]:hover,
    [data-testid="stTopNavSection"]:hover {{
        color: #0F172A !important;
        background-color: #F1F5F9 !important;
    }}

    [data-testid="stTopNavLink"]:hover span,
    [data-testid="stTopNavSection"]:hover span,
    [data-testid="stTopNavLink"]:hover p,
    [data-testid="stTopNavSection"]:hover p {{
        color: #0F172A !important;
    }}

    /* Link ativo no topo (Destaque visual 10%) */
    [data-testid="stTopNavLink"][aria-current="page"],
    [data-testid="stTopNavLinkContainer"] [aria-current="page"] {{
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        border-radius: 0.5rem !important;
        border: 1px solid #CBD5E1 !important;
    }}

    [data-testid="stTopNavLink"][aria-current="page"] span,
    [data-testid="stTopNavLink"][aria-current="page"] p {{
        color: #0F172A !important;
        font-weight: 600 !important;
    }}

    [data-testid="stTopNavLink"][aria-current="page"] [data-testid="stIconMaterial"] {{
        color: #10B981 !important;
    }}

    [data-testid="stExpandSidebarButton"] span {{
        color: #475569 !important;
    }}
    [data-testid="stExpandSidebarButton"]:hover span {{
        color: #0F172A !important;
    }}

    /* Previne barra de rolagem horizontal com elementos full-width */
    [data-testid="stAppViewContainer"],
    .stApp,
    section[data-testid="stMain"] {{
        overflow-x: hidden !important;
    }}

    /* Container principal da aplicação com espaçamento consistente */
    [data-testid="stMainBlockContainer"] {{
        max-width: 1240px;
        padding: 4.8rem 2rem 3rem;
    }}

    /* Rodapé global: ocupa 100% da largura da tela, exatamente como o topo */
    .app-global-footer-wrapper {{
        width: 100vw !important;
        position: relative !important;
        left: 50% !important;
        right: 50% !important;
        margin-left: -50vw !important;
        margin-right: -50vw !important;
        margin-top: 5rem !important;
        margin-bottom: -3rem !important;
        background-color: #FFFFFF !important;
        border-top: 1px solid #CBD5E1 !important;
        box-shadow: 0 -1px 3px 0 rgba(15, 23, 42, 0.04) !important;
        box-sizing: border-box !important;
    }}

    .app-global-footer-content {{
        max-width: 1240px;
        margin: 0 auto;
        padding: 2.2rem 2rem 1.8rem 2rem;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 1.5rem;
        box-sizing: border-box;
    }}

    /* Oculta iframe de sincronização de storage para evitar layout shift */
    iframe[height="0"] {{
        display: none !important;
        position: absolute !important;
        height: 0 !important;
        width: 0 !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Títulos em Azul Noturno com peso forte */
    h1, h2, h3, h4, h5, h6 {{
        color: {THEME_TOKENS['text_primary']} !important;
        letter-spacing: -0.02em;
    }}

    /* Estilização refinada dos containers com borda (Cards) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: {THEME_TOKENS['bg_card']} !important;
        border-color: {THEME_TOKENS['border']} !important;
        border-radius: {THEME_TOKENS['radius']} !important;
        box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04) !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {{
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08) !important;
    }}

    /* Botões Primários em Verde-menta (10% Destaques) */
    button[kind="primary"],
    [data-testid="stBaseButton-primary"] {{
        background-color: {THEME_TOKENS['accent_mint']} !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: {THEME_TOKENS['radius']} !important;
        box-shadow: 0 1px 2px 0 rgba(16, 185, 129, 0.3) !important;
        transition: background-color 0.2s ease, transform 0.1s ease !important;
    }}

    button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {{
        background-color: {THEME_TOKENS['accent_mint_hover']} !important;
    }}

    button[kind="primary"]:active,
    [data-testid="stBaseButton-primary"]:active {{
        transform: scale(0.98);
    }}

    /* Botões Secundários / Terciários Neutros */
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {{
        border-color: {THEME_TOKENS['border']} !important;
        color: {THEME_TOKENS['text_primary']} !important;
        border-radius: {THEME_TOKENS['radius']} !important;
    }}

    /* Foco acessível em campos de texto e áreas de edição */
    input:focus, textarea:focus {{
        border-color: {THEME_TOKENS['border_focus']} !important;
        box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2) !important;
        outline: none !important;
    }}

    /* Métricas: superfície clara e bordas sutis */
    [data-testid="stMetric"] {{
        background-color: {THEME_TOKENS['bg_surface']} !important;
        padding: 0.8rem 1rem !important;
        border-radius: {THEME_TOKENS['radius']} !important;
        border: 1px solid {THEME_TOKENS['border']} !important;
    }}

    /* Itens da lista na barra lateral */
    [data-testid="stSidebar"] .stButton button {{
        justify-content: flex-start;
        text-align: left;
        width: 100%;
        border-radius: {THEME_TOKENS['radius']};
    }}

    /* Avatar do usuário com gradiente tecnológico */
    .gm-avatar {{
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, {THEME_TOKENS['text_primary']} 0%, {THEME_TOKENS['accent_cyan']} 60%, {THEME_TOKENS['accent_mint']} 100%);
        color: #FFFFFF;
        font-size: 1.4rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.15);
    }}

    @page {{
        size: A4 portrait;
        margin: 0;
    }}

    /* Regras de impressão limpa da aplicação: oculta navegação, sidebar, botões e rodapé global */
    @media print {{
        header,
        footer,
        nav,
        [data-testid="stHeader"],
        [data-testid="stSidebar"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stExpandSidebarButton"],
        .app-global-footer-wrapper,
        .app-global-footer,
        .app-global-footer-content,
        .stTabs [role="tablist"],
        button,
        [data-testid="stButton"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        .no-print {{
            display: none !important;
        }}

        [data-testid="stAppViewContainer"],
        [data-testid="stMainBlockContainer"],
        section[data-testid="stMain"],
        .stApp {{
            background: #FFFFFF !important;
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
            overflow: visible !important;
        }}

        @page {{
            size: A4 portrait;
            margin: 0;
        }}

        a {{
            text-decoration: none !important;
            color: inherit !important;
        }}

        a[href]:after {{
            content: none !important;
        }}
    }}
</style>
"""

def apply_theme():
    """Injeta o CSS global complementar ao tema nativo."""
    st.markdown(_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    """
    Cabeçalho padrão de página (título em Azul Noturno + subtítulo explicativo).
    Retorna a coluna da direita para botões de ação primária da tela.
    """
    col_title, col_actions = st.columns([3, 1], vertical_alignment="bottom")
    with col_title:
        st.header(title, anchor=False)
        if subtitle:
            st.caption(subtitle)
    return col_actions

def login_gate(title: str, message: str, key: str):
    """Bloqueio padronizado para páginas restritas a usuários autenticados."""
    with st.container(border=True):
        st.warning(f"**{title}**\n\n{message}", icon=":material/lock:")
        with st.container(horizontal=True):
            if st.button("Entrar", type="primary", icon=":material/login:", key=f"{key}_btn_login_auth"):
                set_page("login")
                st.rerun()
            if st.button("Criar conta grátis", type="secondary", icon=":material/person_add:", key=f"{key}_btn_signup_auth"):
                set_page("signup")
                st.rerun()

def resume_input(key: str, default: str = "", height: int = 300) -> str:
    """
    Campo de currículo base com suporte à importação de arquivos (PDF, DOCX, MD, TXT).
    O texto extraído preenche a área de edição com conforto visual para leitura e revisão.
    """
    st.session_state.setdefault(key, default)
    uploaded = st.file_uploader(
        "Importar de arquivo",
        type=["pdf", "docx", "md", "txt"],
        key=f"{key}_file",
        help="O texto é extraído automaticamente para o campo abaixo, onde permanece 100% editável."
    )
    if uploaded is not None and st.session_state.get(f"{key}_file_id") != uploaded.file_id:
        try:
            st.session_state[key] = extract_text_from_file(uploaded)
            st.session_state[f"{key}_file_id"] = uploaded.file_id
            st.toast(f"Texto importado com sucesso de {uploaded.name}", icon=":material/check_circle:")
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo: {e}", icon=":material/error:")

    return st.text_area(
        "Texto do currículo",
        key=key,
        height=height,
        placeholder="Cole seu currículo aqui ou importe um arquivo acima..."
    )

def application_card(r: dict, key: str):
    """Card de candidatura: título em Azul Noturno, metadados legíveis e botão de detalhamento."""
    diag = r.get("diagnostic") or {}
    meta = [history_manager.format_display_date(r.get("date", "")), (r.get("language") or "pt").upper()]
    if "ats_score" in diag:
        meta.append(f"ATS {diag['ats_score']}%")
    if r.get("has_cover_letter"):
        meta.append("com carta")

    with st.container(border=True, horizontal=True, vertical_alignment="center", wrap=False):
        st.markdown(f"**{(r.get('job_title') or 'Vaga').strip()}**  \n:gray[{' · '.join(meta)}]", width="stretch")
        url = r.get("job_url") or ""
        if url.startswith(("http://", "https://")):
            st.link_button("Vaga", url, icon=":material/open_in_new:", type="tertiary", help="Abrir anúncio original da vaga")
        if st.button("Abrir", icon=":material/arrow_forward:", key=key, type="secondary"):
            st.session_state.viewing_history = r["filepath"]
            set_page("applications", clear_transient=False)
            st.rerun()

def render_footer():
    """
    Rodapé institucional global padronizado da aplicação.
    Ocupa 100% da largura da tela (full-width), idêntico à barra superior,
    com conteúdo centralizado e alinhado aos limites da página.
    """
    st.markdown(
        f"""
        <div class="app-global-footer-wrapper app-global-footer">
            <div class="app-global-footer-content">
                <div>
                    <div style="font-weight: 700; color: {THEME_TOKENS['text_primary']}; font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
                        🎯 <span>GitMatch · CV Nitro</span>
                    </div>
                    <div style="font-size: 0.82rem; color: {THEME_TOKENS['text_secondary']}; margin-top: 2px;">
                        Otimizador Inteligente de Currículos com IA Multi-Agente & ATS
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 1.5rem;">
                    <div>
                        Desenvolvido por <strong>Thiago Araújo</strong>
                    </div>
                    <div style="display: flex; gap: 1rem; align-items: center;">
                        <a href="https://github.com/thiagoeu" target="_blank" rel="noopener noreferrer" style="
                            color: {THEME_TOKENS['accent_cyan']};
                            text-decoration: none;
                            font-weight: 600;
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                        ">
                            GitHub @thiagoeu
                        </a>
                        <span style="color: {THEME_TOKENS['border']};">·</span>
                        <a href="mailto:araujo.thiago1051@gmail.com" style="
                            color: {THEME_TOKENS['accent_cyan']};
                            text-decoration: none;
                            font-weight: 600;
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                        ">
                            araujo.thiago1051@gmail.com
                        </a>
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #64748B;">
                    Licença MIT · Projeto acadêmico para Sistemas Multi-Agentes (SMA)
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_storage_sync(token: Optional[str] = None, is_logout: bool = False):
    """
    Sincroniza a credencial de sessão com o localStorage e cookie do navegador via iframe,
    garantindo que o token NÃO fique visível na URL para o usuário.
    - Se autenticado: grava o token assinado no localStorage e limpa resquícios da URL.
    - Se logout: remove o token do localStorage e limpa a URL.
    - Se visitante em recarregamento: detecta o token salvo no localStorage e restaura a sessão.
    """
    import streamlit.components.v1 as components
    clean_token = token or ""
    logout_flag = "true" if is_logout else "false"

    script = f"""
    <script>
    (function() {{
        try {{
            var storageKey = "cv_nitro_auth_token";
            var win = window.parent || window;
            var activeToken = "{clean_token}";
            var isLogout = {logout_flag};

            // 1. Limpeza estética e de privacidade: limpa auth_token da barra de endereço imediatamente
            try {{
                if (win.location.search && win.location.search.indexOf("auth_token=") !== -1) {{
                    var cleanSearch = win.location.search
                        .replace(/[?&]auth_token=[^&]+/, '')
                        .replace(/^&/, '?');
                    if (cleanSearch === '?') cleanSearch = '';
                    var cleanUrl = win.location.pathname + cleanSearch + win.location.hash;
                    win.history.replaceState(null, '', cleanUrl);
                }}
            }} catch(e) {{}}

            if (isLogout) {{
                try {{ win.localStorage.removeItem(storageKey); }} catch(e) {{}}
                try {{ window.localStorage.removeItem(storageKey); }} catch(e) {{}}
                try {{ win.document.cookie = storageKey + "=; path=/; max-age=0"; }} catch(e) {{}}
                try {{ document.cookie = storageKey + "=; path=/; max-age=0"; }} catch(e) {{}}
            }} else if (activeToken && activeToken.length > 10) {{
                try {{ win.localStorage.setItem(storageKey, activeToken); }} catch(e) {{}}
                try {{ window.localStorage.setItem(storageKey, activeToken); }} catch(e) {{}}
                try {{ win.document.cookie = storageKey + "=" + encodeURIComponent(activeToken) + "; path=/; max-age=2592000; SameSite=Lax"; }} catch(e) {{}}
            }} else {{
                var savedToken = null;
                try {{ savedToken = win.localStorage.getItem(storageKey); }} catch(e) {{}}
                if (!savedToken) {{
                    try {{ savedToken = window.localStorage.getItem(storageKey); }} catch(e) {{}}
                }}
                if (!savedToken) {{
                    try {{
                        var match = (win.document.cookie || document.cookie).match(new RegExp('(^| )' + storageKey + '=([^;]+)'));
                        if (match) savedToken = decodeURIComponent(match[2]);
                    }} catch(e) {{}}
                }}
                var loc = win.location;
                if (savedToken && savedToken.length > 10) {{
                    var hasTokenParam = loc.search && loc.search.indexOf("auth_token=") !== -1;
                    var isLogoutParam = loc.search && loc.search.indexOf("action=logout") !== -1;
                    if (!hasTokenParam && !isLogoutParam) {{
                        var joinChar = loc.search ? "&" : "?";
                        loc.replace(loc.pathname + loc.search + joinChar + "auth_token=" + encodeURIComponent(savedToken));
                    }}
                }}
            }}
        }} catch(e) {{
            // Silencioso em caso de restrições de sandbox
        }}
    }})();
    </script>
    """
    try:
        components.html(script, height=0)
    except Exception:
        pass

