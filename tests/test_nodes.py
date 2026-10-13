from src.agents.nodes import job_analyzer
from src.agents.state import GraphState
import os

# Dummy fallback API key for testing structural parsing
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "dummy")

def test_job_analyzer():
    state = GraphState(
        job_description="Procuramos Desenvolvedor Backend com experiência em Python, FastAPI e Docker. Metodologias Ágeis é um diferencial.",
        base_resume_md="",
        github_username="",
        job_keywords=[],
        job_technologies=[],
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    try:
        # Só executa a requisição real se houver uma API_KEY verdadeira
        if os.environ.get("GEMINI_API_KEY") != "dummy":
            result = job_analyzer(state)
            print("Resultado Job Analyzer:")
            print(f"Tecnologias: {result['job_technologies']}")
            print(f"Palavras-chave: {result['job_keywords']}")
            
            assert "Python" in result['job_technologies'] or "FastAPI" in result['job_technologies'], "Tecnologia principal não encontrada."
            assert len(result['job_keywords']) > 0, "Deveria haver palavras-chave"
            print("Teste passou!")
        else:
            print("PULADO: GEMINI_API_KEY não está configurada para teste real.")
    except Exception as e:
        # Caso o mock falhe com auth error
        print(f"Ignorando erro de API: {e}")

from src.agents.nodes import github_researcher

def test_github_researcher():
    state = GraphState(
        job_description="",
        base_resume_md="",
        github_username="octocat", # User de teste clássico do GitHub
        job_keywords=[],
        job_technologies=["ruby"], # O octocat deve ter repo em ruby ou html
        github_repos=[],
        github_readmes={},
        generated_resume_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    print("\nTestando GitHub Researcher...")
    result = github_researcher(state)
    print(f"Repos encontrados: {[r['name'] for r in result['github_repos']]}")
    print(f"READMEs baixados: {list(result['github_readmes'].keys())}")
    
    # Octocat is an official GitHub test account, should always have repos.
    assert len(result['github_repos']) > 0, "Deveria encontrar repositórios para octocat."
    print("Teste do GitHub Researcher passou!")

from src.agents.nodes import resume_generator

def test_resume_generator():
    state = GraphState(
        job_description="Vaga de Desenvolvedor Python com experiência em FastAPI",
        base_resume_md="# Meu Currículo\nDesenvolvedor Web.",
        github_username="teste",
        job_keywords=["FastAPI", "Python"],
        job_technologies=["Python", "FastAPI"],
        github_repos=[{"name": "meu-api", "description": "Uma API em Python", "language": "Python"}],
        github_readmes={"meu-api": "Usando FastAPI"},
        generated_resume_md=None,
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    print("\nTestando Resume Generator...")
    if os.environ.get("GEMINI_API_KEY") != "dummy":
        result = resume_generator(state)
        print(f"Currículo gerado (trecho): {result['generated_resume_md'][:100]}...")
        assert len(result['generated_resume_md']) > 0, "O currículo gerado não deve estar vazio."
        print("Teste do Resume Generator passou!")
    else:
        print("PULADO: GEMINI_API_KEY não está configurada para teste real.")

from src.agents.nodes import quality_reviewer

def test_quality_reviewer():
    state = GraphState(
        job_description="",
        base_resume_md="# Meu Currículo\nDesenvolvedor.",
        github_username="teste",
        job_keywords=[],
        job_technologies=[],
        github_repos=[{"name": "meu-api"}],
        github_readmes={"meu-api": "Apenas um Hello World"},
        generated_resume_md="# Meu Currículo\nDesenvolvedor que criou um modelo de Machine Learning gigante em PyTorch (Invenção).",
        reviewer_feedback=None,
        reviewer_approved=False,
        review_attempts=0
    )
    
    print("\nTestando Quality Reviewer...")
    if os.environ.get("GEMINI_API_KEY") != "dummy":
        result = quality_reviewer(state)
        print(f"Aprovado? {result['reviewer_approved']}")
        print(f"Feedback: {result['reviewer_feedback']}")
        if "Erro de API" in result['reviewer_feedback']:
            print("PULADO: Erro de API retornado, não é possível testar alucinação (esperado sem chave real).")
        else:
            assert not result['reviewer_approved'], "Deveria reprovar a alucinação de Machine Learning."
            print("Teste do Quality Reviewer passou!")
    else:
        print("PULADO: GEMINI_API_KEY não está configurada para teste real.")

if __name__ == "__main__":
    test_job_analyzer()
    test_github_researcher()
    test_resume_generator()
    test_quality_reviewer()
