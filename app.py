import streamlit as st
from src.core import history_manager, auth_manager
from src.agents.graph import build_graph
from src.ui.navbar import render_navbar, set_page, get_current_page, clear_transient_state
from src.ui.dashboard_view import render_dashboard_view
from src.ui.wizard_view import render_wizard_view
from src.ui.applications_view import render_applications_view, render_applications_list as ui_render_apps_list
from src.ui.settings_view import render_settings_view
from src.ui.auth_views import render_login_view, render_signup_view

# 1. Configuração da Página
st.set_page_config(
    page_title="GitMatch - CV Nitro Optimizer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS Global: Remove header, deploy, menu nativo e setinhas de colapso
st.markdown("""
<style>
    /* Oculta completamente o header nativo do Streamlit, deploy, menu e a setinha keyboard_double_arrow_right */
    header[data-testid="stHeader"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        width: 0px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Remove espaçamentos vazios deixados pelo header e posiciona a navbar no topo */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Compilação do Grafo Multi-Agente
graph = build_graph()

# 3. Inicialização do Estado de Sessão
if "user_session" not in st.session_state:
    st.session_state.user_session = auth_manager.create_guest_session()
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

# 4. Funções de Cache de Alta Performance
@st.cache_data(ttl=30, show_spinner=False)
def get_cached_resumes(user_id: str = "guest_local"):
    """Recupera lista de candidaturas com cache curto para resposta instantânea."""
    return history_manager.list_resumes(user_id=user_id)

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_application(filepath: str):
    """Carrega dados da aplicação com cache em memória para visualização sem latência."""
    return history_manager.load_application(filepath)

def clear_history_cache():
    """Invalida o cache após salvar, atualizar ou excluir candidaturas."""
    get_cached_resumes.clear()
    get_cached_application.clear()

def render_sidebar(resumes: list = None):
    """Renderiza a barra lateral dedicada exclusivamente ao Acesso Rápido aos currículos."""
    if resumes is None:
        uid = st.session_state.user_session.get("user_id", "guest_local") if "user_session" in st.session_state else "guest_local"
        resumes = get_cached_resumes(uid)

    st.sidebar.markdown("### ⚡ Acesso Rápido")
    st.sidebar.caption("🕒 Mais recentes primeiro:")
    
    if not resumes:
        st.sidebar.caption("Nenhuma candidatura recente.")
        return

    for idx, r in enumerate(resumes[:8]):
        date_str = history_manager.format_display_date(r.get("date", ""))
        title = r.get("job_title", "Vaga")
        lang = (r.get("language") or "pt").upper()
        btn_label = f"[{lang}] {title[:14]}... ({date_str})"
        
        if st.sidebar.button(btn_label, key=f"sb_quick_{idx}", use_container_width=True):
            st.session_state.viewing_history = r["filepath"]
            set_page("applications", clear_transient=False)
            st.rerun()

# Wrappers de compatibilidade retroativa para testes e integrações externas
def render_dashboard(resumes: list):
    render_dashboard_view(resumes)

def render_settings():
    render_settings_view(clear_history_cache)

def render_applications_list(resumes: list):
    ui_render_apps_list(resumes)

def main():
    current_uid = st.session_state.user_session.get("user_id", "guest_local")
    resumes = get_cached_resumes(current_uid)
    
    # Barra lateral focada em Acesso Rápido
    render_sidebar(resumes)
    
    # Barra Superior Moderna no padrão SaaS
    page = render_navbar()
    
    # Roteador Desacoplado de Views
    if page == "dashboard":
        render_dashboard_view(resumes)
    elif page == "wizard":
        render_wizard_view(graph, clear_history_cache)
    elif page == "applications":
        render_applications_view(resumes, get_cached_application, clear_history_cache, graph)
    elif page == "settings":
        render_settings_view(clear_history_cache)
    elif page == "login":
        render_login_view(on_success_callback=clear_history_cache)
    elif page == "signup":
        render_signup_view(on_success_callback=clear_history_cache)
    else:
        render_dashboard_view(resumes)

if __name__ == "__main__":
    main()
