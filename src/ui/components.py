import streamlit as st
from src.core import history_manager
from src.core.document_parser import extract_text_from_file
from src.ui.navbar import set_page

# Cores, raios e fonte vêm do tema em .streamlit/config.toml; aqui só o que o tema não cobre.
_CSS = """
<style>
    /* Remove apenas elementos do Streamlit que não fazem parte do produto */
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"],
    #MainMenu,
    [data-testid="stDecoration"],
    footer {
        display: none !important;
    }

    /* O header nativo é a navbar: superfície sólida e borda inferior */
    header[data-testid="stHeader"] {
        background: rgba(11, 16, 32, 0.92);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid #263149;
    }

    /* Mesma largura e respiro em todas as páginas */
    [data-testid="stMainBlockContainer"] {
        max-width: 1240px;
        padding: 5rem 2rem 3rem;
    }

    /* Itens da lista "Recentes" na sidebar alinhados à esquerda */
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stButton button > div,
    [data-testid="stSidebar"] .stButton button > div > span,
    [data-testid="stSidebar"] .stButton button p {
        justify-content: flex-start;
        text-align: left;
        width: 100%;
    }

    .gm-avatar {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: #fff;
        font-size: 1.4rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
"""

def apply_theme():
    """Injeta o CSS global complementar ao tema."""
    st.markdown(_CSS, unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    """
    Cabeçalho padrão de página (título + subtítulo à esquerda).
    Retorna a coluna da direita para botões de ação da página.
    """
    col_title, col_actions = st.columns([3, 1], vertical_alignment="bottom")
    with col_title:
        st.header(title, anchor=False)
        if subtitle:
            st.caption(subtitle)
    return col_actions

def login_gate(title: str, message: str, key: str):
    """Bloqueio padrão para páginas que exigem login, com atalhos para entrar ou cadastrar."""
    with st.container(border=True):
        st.warning(f"**{title}**\n\n{message}", icon=":material/lock:")
        with st.container(horizontal=True):
            if st.button("Entrar", type="primary", icon=":material/login:", key=f"{key}_btn_login_auth"):
                set_page("login")
                st.rerun()
            if st.button("Criar conta grátis", icon=":material/person_add:", key=f"{key}_btn_signup_auth"):
                set_page("signup")
                st.rerun()

def resume_input(key: str, default: str = "", height: int = 300) -> str:
    """
    Campo de currículo com importação de arquivo (PDF, DOCX, MD, TXT).
    O texto extraído preenche o campo, que continua editável. Retorna o texto atual.
    """
    st.session_state.setdefault(key, default)
    uploaded = st.file_uploader(
        "Importar de arquivo",
        type=["pdf", "docx", "md", "txt"],
        key=f"{key}_file",
        help="O texto é extraído e colocado no campo abaixo, onde você pode revisar."
    )
    # Só aplica cada arquivo uma vez, para não sobrescrever edições feitas depois do upload
    if uploaded is not None and st.session_state.get(f"{key}_file_id") != uploaded.file_id:
        try:
            st.session_state[key] = extract_text_from_file(uploaded)
            st.session_state[f"{key}_file_id"] = uploaded.file_id
            st.toast(f"Texto importado de {uploaded.name}", icon=":material/check_circle:")
        except Exception as e:
            st.error(f"Não foi possível ler o arquivo: {e}", icon=":material/error:")

    return st.text_area(
        "Texto do currículo",
        key=key,
        height=height,
        placeholder="Cole seu currículo aqui ou importe um arquivo acima..."
    )

def application_card(r: dict, key: str):
    """Linha de candidatura: título, metadados, link externo e botão para abrir o detalhe."""
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
            st.link_button("Vaga", url, icon=":material/open_in_new:", type="tertiary", help="Abrir anúncio da vaga")
        if st.button("Abrir", icon=":material/arrow_forward:", key=key):
            st.session_state.viewing_history = r["filepath"]
            set_page("applications", clear_transient=False)
            st.rerun()
