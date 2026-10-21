from langgraph.graph import StateGraph, END
from src.agents.state import GraphState
from src.agents.nodes import (
    job_analyzer,
    github_researcher,
    resume_generator,
    quality_reviewer,
    cover_letter_generator,
    MAX_REVIEW_ATTEMPTS
)

def route_after_review(state: dict) -> str:
    """
    Decide se o fluxo gera a Cover Letter após aprovação ou se esgotou as tentativas,
    ou se encerra diretamente quando generate_cover_letter é False, ou se volta para o gerador.
    """
    if state.get("reviewer_approved", False) or state.get("review_attempts", 0) >= MAX_REVIEW_ATTEMPTS:
        if state.get("generate_cover_letter", True) is False:
            return END
        return "cover_letter_generator"
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
    workflow.add_node("cover_letter_generator", cover_letter_generator)
    
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
            "cover_letter_generator": "cover_letter_generator",
            "resume_generator": "resume_generator",
            END: END
        }
    )
    
    # A Cover Letter finaliza o fluxo
    workflow.add_edge("cover_letter_generator", END)
    
    # Compila o grafo
    return workflow.compile()

if __name__ == "__main__":
    print("Construindo grafo...")
    app = build_graph()
    print("Grafo construído com sucesso.")
