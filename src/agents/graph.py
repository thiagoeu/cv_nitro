from langgraph.graph import StateGraph, START, END
from src.agents.state import GraphState
from src.agents.nodes import (
    job_analyzer,
    github_fetcher,
    relevance_ranker,
    github_researcher,
    resume_generator,
    section_patcher,
    quality_reviewer,
    cover_letter_generator,
    MAX_REVIEW_ATTEMPTS
)

def route_after_review(state: dict) -> str:
    """
    Decide o roteamento após a auditoria de qualidade:
    - Se aprovado ou excedeu o limite de tentativas: encerra (END) ou gera a cover letter.
    - Se rejeitado com severidade 'minor' e seção alvo identificada: aciona 'section_patcher'.
    - Se rejeitado com severidade 'major': aciona regeneração completa via 'resume_generator'.
    """
    if state.get("reviewer_approved", False) or state.get("review_attempts", 0) >= MAX_REVIEW_ATTEMPTS:
        if state.get("generate_cover_letter", True) is False:
            return END
        return "cover_letter_generator"
    
    severity = state.get("review_severity", "major")
    target_section = state.get("patch_section")
    
    if severity == "minor" and target_section:
        return "section_patcher"
    
    return "resume_generator"

def build_graph():
    # Cria o grafo com o estado
    workflow = StateGraph(GraphState)
    
    # Adiciona os nós
    workflow.add_node("job_analyzer", job_analyzer)
    workflow.add_node("github_fetcher", github_fetcher)
    workflow.add_node("relevance_ranker", relevance_ranker)
    workflow.add_node("resume_generator", resume_generator)
    workflow.add_node("section_patcher", section_patcher)
    workflow.add_node("quality_reviewer", quality_reviewer)
    workflow.add_node("cover_letter_generator", cover_letter_generator)
    
    # Fan-out concorrente a partir do início (START)
    workflow.add_edge(START, "job_analyzer")
    workflow.add_edge(START, "github_fetcher")
    
    # Convergência (Scatter-Gather) em relevance_ranker
    workflow.add_edge("job_analyzer", "relevance_ranker")
    workflow.add_edge("github_fetcher", "relevance_ranker")
    
    # Sequência de geração e revisão
    workflow.add_edge("relevance_ranker", "resume_generator")
    workflow.add_edge("resume_generator", "quality_reviewer")
    
    # Seção cirúrgica retorna ao revisor para checagem rápida
    workflow.add_edge("section_patcher", "quality_reviewer")
    
    # Adiciona a condição de loop de revisão
    workflow.add_conditional_edges(
        "quality_reviewer",
        route_after_review,
        {
            "cover_letter_generator": "cover_letter_generator",
            "section_patcher": "section_patcher",
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
