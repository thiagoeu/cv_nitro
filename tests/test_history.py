from src.core import history_manager
import os

def test_history_manager():
    print("Testing save_resume...")
    filepath = history_manager.save_resume("Desenvolvedor Python Pleno", "# Meu Currículo Python\nExperiência com LangGraph.")
    print(f"File saved to {filepath}")
    
    assert os.path.exists(filepath), "File was not created."
    
    print("Testing list_resumes...")
    resumes = history_manager.list_resumes()
    print(f"Found {len(resumes)} resumes.")
    assert len(resumes) >= 1, "Resume list should not be empty."
    
    latest_resume = resumes[0]
    print(f"Latest resume job title: {latest_resume['job_title']}")
    assert latest_resume['job_title'] == "Desenvolvedor Python Pleno"
    
    print("Testing load_resume...")
    content = history_manager.load_resume(latest_resume["filepath"])
    print(f"Loaded content: {content[:20]}...")
    assert "# Meu Currículo" in content, "Content was not correctly loaded."
    
    print("All tests passed!")

if __name__ == "__main__":
    test_history_manager()
