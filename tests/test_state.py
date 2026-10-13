from src.agents.state import GraphState

def test_graph_state():
    state = GraphState(
        job_description="Vaga de Teste",
        base_resume_md="# Meu CV",
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
    
    print("State creation successful.")
    print(f"Job Description: {state['job_description']}")
    print(f"Attempts: {state['review_attempts']}")
    assert state['job_description'] == "Vaga de Teste"

if __name__ == "__main__":
    test_graph_state()
