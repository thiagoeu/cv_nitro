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
        review_attempts=0,
        generate_cover_letter=True,
        strict_review=True,
        diagnostic={"ats_score": 85, "matched_keywords": ["python"]},
        best_resume_md=None,
        best_ats_score=None,
        best_diagnostic=None,
        stop_reason=None,
        agent_trace=[]
    )
    
    print("State creation successful.")
    print(f"Job Description: {state['job_description']}")
    print(f"Attempts: {state['review_attempts']}")
    assert state['job_description'] == "Vaga de Teste"
    assert state['generate_cover_letter'] is True
    assert state['strict_review'] is True
    assert state['diagnostic']['ats_score'] == 85
    assert state['agent_trace'] == []
    assert state['best_resume_md'] is None

if __name__ == "__main__":
    test_graph_state()
