from langgraph.graph import StateGraph, END
from src.agents.state import GraphState
from src.agents.nodes import job_analyzer, github_researcher, resume_generator, quality_reviewer

def route_after_review(state: dict) -> str:
    """
    Decide se o fluxo acaba ou volta pro gerador.
    """
    if state.get("reviewer_approved", False):
        return END
    else:
        return "resume_generator"

def build_graph():
    # Cria o grafo com o estado
    workflow = StateGraph(GraphState)
    
    # Adiciona os nós
    workflow.add_node("job_analyzer", job_analyzer)
    workflow.add_node("github_researcher", github_researcher)
    workflow.add_node("resume_generator", resume_generator)
    workflow.add_node("quality_reviewer", quality_reviewer)
    
    # Define o ponto de entrada
    workflow.set_entry_point("job_analyzer")
    
    # Define as conexões (arestas)
    workflow.add_edge("job_analyzer", "github_researcher")
    workflow.add_edge("github_researcher", "resume_generator")
    workflow.add_edge("resume_generator", "quality_reviewer")
    
    # Adiciona a condição de loop
    workflow.add_conditional_edges(
        "quality_reviewer",
        route_after_review,
        {
            END: END,
            "resume_generator": "resume_generator"
        }
    )
    
    # Compila o grafo
    return workflow.compile()

if __name__ == "__main__":
    print("Construindo grafo...")
    app = build_graph()
    print("Grafo construído com sucesso.")
    
    # Teste Dry-Run
    print("Iniciando dry-run end-to-end...")
    initial_state = GraphState(
        job_description="Dev",
        base_resume_md="Teste",
        github_username="octocat",
        job_keywords=[],
        job_technologies=[],
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    # Rodamos mas ignorando se der erro por falta de chave de API, pois só queremos validar o grafo compilando
    try:
        final_state = app.invoke(initial_state)
        print("Dry-run concluído.")
        print(f"Aprovado final: {final_state.get('reviewer_approved')}")
    except Exception as e:
        print(f"Erro durante a execução (provável falta de API_KEY válida): {e}")
