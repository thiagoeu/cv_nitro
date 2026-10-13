import streamlit as st
from src.core import history_manager
from src.agents.graph import build_graph
from src.agents.state import GraphState

# Configuração da página
st.set_page_config(page_title="GitMatch - CV Optimizer", layout="wide")

# Inicializando o grafo
@st.cache_resource
def get_graph():
    return build_graph()

graph = get_graph()

def render_sidebar():
    st.sidebar.title("📚 Histórico de Currículos")
    st.sidebar.markdown("---")
    
    resumes = history_manager.list_resumes()
    
    if not resumes:
        st.sidebar.info("Nenhum currículo gerado ainda.")
        return
        
    for idx, resume in enumerate(resumes):
        date_str = resume.get('date', '')[:10]
        job_title = resume.get('job_title', 'Vaga Desconhecida')
        
        if st.sidebar.button(f"{date_str} - {job_title}", key=f"hist_{idx}"):
            st.session_state.viewing_history = resume['filepath']

def main():
    st.title("🎯 GitMatch - Otimizador Inteligente de Currículo")
    st.write("Insira os dados da vaga e seu usuário do GitHub para gerar um currículo focado.")
    
    # Renderiza a sidebar
    render_sidebar()
    
    # Se clicou num item do histórico, exibe ele e ignora o formulário
    if "viewing_history" in st.session_state:
        st.info("Visualizando currículo do histórico.")
        if st.button("← Voltar para criar novo"):
            del st.session_state.viewing_history
            st.rerun()
            
        content = history_manager.load_resume(st.session_state.viewing_history)
        st.markdown(content)
        return

    # Formulário principal
    with st.form("resume_form"):
        job_title = st.text_input("Título da Vaga (ex: Desenvolvedor Python)")
        job_desc = st.text_area("Descrição da Vaga", height=200)
        github_user = st.text_input("Usuário do GitHub (ex: defunkt)")
        base_resume = st.text_area("Seu Currículo Atual (Markdown)", height=200)
        
        submit = st.form_submit_button("Gerar Currículo Otimizado 🚀")
        
    if submit:
        if not job_title or not job_desc or not base_resume:
            st.error("Preencha todos os campos obrigatórios!")
            return
            
        st.info("Processando com LangGraph... (Isso pode levar alguns minutos)")
        
        initial_state = GraphState(
            job_description=job_desc,
            base_resume_md=base_resume,
            github_username=github_user,
            job_keywords=[],
            job_technologies=[],
            github_repos=[],
            github_readmes={},
            generated_resume_md=None,
            reviewer_feedback=None,
            reviewer_approved=False,
            review_attempts=0
        )
        
        with st.spinner("Agentes trabalhando..."):
            try:
                final_state = graph.invoke(initial_state)
                generated_md = final_state.get("generated_resume_md", "")
                
                if final_state.get("reviewer_approved"):
                    st.success("Currículo gerado e aprovado pelo revisor!")
                else:
                    st.warning("O currículo foi gerado, mas atingiu o limite de tentativas de revisão. Verifique o resultado.")
                    
                # Salva no histórico
                history_manager.save_resume(job_title, generated_md)
                
                st.markdown("### Resultado:")
                st.markdown(generated_md)
            except Exception as e:
                st.error(f"Erro durante a execução: {e}")

if __name__ == "__main__":
    main()
