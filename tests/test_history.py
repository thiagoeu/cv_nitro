from src.core import history_manager
import os

def test_history_manager():
    print("Testing save_resume com novos campos...")
    filepath = history_manager.save_resume(
        job_title="Senior Python Engineer",
        content="# My Resume\nPython, AI, Cloud.",
        job_url="https://linkedin.com/jobs/view/9999",
        cover_letter="Dear Team,\n\nI love this role.",
        language="en",
        technologies=["Python", "LangGraph"]
    )
    print(f"File saved to {filepath}")
    
    assert os.path.exists(filepath), "File was not created."
    
    print("Testing list_resumes...")
    resumes = history_manager.list_resumes()
    assert len(resumes) >= 1, "Resume list should not be empty."
    
    latest_resume = resumes[0]
    assert latest_resume['job_title'] == "Senior Python Engineer"
    assert latest_resume.get('job_url') == "https://linkedin.com/jobs/view/9999"
    assert latest_resume.get('language') == "en"
    
    print("Testing load_resume (retrocompatibilidade)...")
    resume_only = history_manager.load_resume(latest_resume["filepath"])
    assert "# My Resume" in resume_only
    assert "Dear Team" not in resume_only, "load_resume não deve incluir a Cover Letter."
    
    print("Testing load_application...")
    app_data = history_manager.load_application(latest_resume["filepath"])
    assert app_data["resume_md"].startswith("# My Resume")
    assert "Dear Team" in app_data["cover_letter_md"]
    assert app_data["metadata"]["job_url"] == "https://linkedin.com/jobs/view/9999"
    
    print("All history tests passed!")

if __name__ == "__main__":
    test_history_manager()
