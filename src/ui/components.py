import streamlit as st
from typing import Optional
from src.core import history_manager, auth_manager
from src.core.document_parser import extract_text_from_file
from src.ui.navbar import set_page
from src.ui.theme import THEME_TOKENS, _CSS, apply_theme, render_footer

SESSION_COOKIE = "cv_nitro_auth_token"


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


def render_storage_sync(token: Optional[str] = None, is_logout: bool = False):
    """
    Grava o cookie de sessão no login e o expira no logout, via iframe com acesso ao documento pai.
    No F5 o navegador envia o cookie na requisição inicial, lida em st.context.cookies.
    """
    if not token and not is_logout:
        return
    import streamlit.components.v1 as components
    max_age = 0 if is_logout else auth_manager.SESSION_TTL_SECONDS
    script = f"""
    <script>
    (function() {{
        var win = window.parent || window;
        var secure = win.location.protocol === "https:" ? "; Secure" : "";
        win.document.cookie = "{SESSION_COOKIE}=" + encodeURIComponent("{token or ''}") +
            "; path=/; max-age={max_age}; SameSite=Strict" + secure;
    }})();
    </script>
    """
    try:
        components.html(script, height=0)
    except Exception:
        pass


def notify_saved(saved_path: str, message: str):
    """Confirma o salvamento; com Supabase ativo, caminho local significa que a sincronização com a nuvem falhou."""
    if history_manager.is_supabase_configured() and not saved_path.startswith("supabase:"):
        st.toast("Salvo apenas localmente: não foi possível sincronizar com a nuvem. Tente salvar novamente mais tarde.", icon=":material/cloud_off:")
    else:
        st.toast(message, icon=":material/check_circle:")
