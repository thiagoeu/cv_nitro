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

def test_history_manager_update_and_rerun_fields():
    filepath = history_manager.save_resume(
        job_title="Full Stack Engineer",
        content="# Initial Resume",
        job_url="https://example.com/job/1",
        cover_letter="Cover Letter",
        language="pt",
        technologies=["Python", "React"],
        job_description="Job description details...",
        base_resume="# Base Resume Text",
        github_username="thiagoeu"
    )
    
    app_data = history_manager.load_application(filepath)
    assert app_data["metadata"]["job_description"] == "Job description details..."
    assert app_data["metadata"]["base_resume"] == "# Base Resume Text"
    assert app_data["metadata"]["github_username"] == "thiagoeu"
    
    # Atualiza no mesmo caminho de arquivo (re-execução/rerun)
    updated_filepath = history_manager.save_resume(
        job_title="Full Stack Engineer",
        content="# Updated Optimized Resume",
        job_url="https://example.com/job/1",
        cover_letter="Updated Letter",
        filepath=filepath
    )
    assert updated_filepath == filepath
    updated_app = history_manager.load_application(filepath)
    assert updated_app["resume_md"] == "# Updated Optimized Resume"
    assert updated_app["cover_letter_md"] == "Updated Letter"

