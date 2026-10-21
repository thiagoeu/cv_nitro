import streamlit as st
from src.ui import navbar

def test_navbar_page_navigation():
    # Testa página padrão
    st.session_state.clear()
    assert navbar.get_current_page() == "dashboard"
    
    # Navega para wizard
    navbar.set_page("wizard")
    assert navbar.get_current_page() == "wizard"
    assert st.session_state.current_page == "wizard"
    
    # Navega para applications
    navbar.set_page("applications")
    assert navbar.get_current_page() == "applications"
    # A troca efetiva fica pendente para o render_navbar() aplicar no próximo rerun
    assert st.session_state["_nav_target"] == "applications"

def test_navbar_clear_transient_state():
    st.session_state.clear()
    st.session_state.transient_error = "Erro anterior que deve ser limpo"
    st.session_state.wizard_errors = ["Campo vazio"]
    st.session_state.search_error = "Vaga não encontrada"
    st.session_state.other_persisted_data = "permanece"
    
    navbar.clear_transient_state()
    
    assert st.session_state.transient_error is None
    assert st.session_state.wizard_errors is None
    assert st.session_state.search_error is None
    assert st.session_state.other_persisted_data == "permanece"

def test_navbar_set_page_closes_viewing_history():
    st.session_state.clear()
    st.session_state.viewing_history = "some_file.json"
    
    # Navegar para página diferente de 'applications' fecha a visualização de detalhe
    navbar.set_page("dashboard")
    assert "viewing_history" not in st.session_state
    
    # Se já estiver em applications, set_page('applications') não deleta se não quiser
    st.session_state.viewing_history = "app_detail.json"
    navbar.set_page("applications")
    assert st.session_state.viewing_history == "app_detail.json"
