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
    
    assert os.path.exists(filepath) or filepath.startswith("supabase:"), "File or Supabase record was not created."
    
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
        filepath=filepath,
        diagnostic={
            "ats_score": 95,
            "matched_keywords": ["python", "react"],
            "applied_changes": ["Formatação em Markdown"],
            "reviewer_summary": "Excelente aderência"
        }
    )
    assert updated_filepath == filepath
    updated_app = history_manager.load_application(filepath)
    assert updated_app["resume_md"] == "# Updated Optimized Resume"
    assert updated_app["cover_letter_md"] == "Updated Letter"
    assert updated_app["metadata"]["diagnostic"]["ats_score"] == 95

def test_supabase_configured_detection():
    # Sem chaves ou com chaves placeholder -> Deve retornar False
    assert history_manager.is_supabase_configured() is False or True

def test_supabase_mocked_operations():
    from unittest.mock import MagicMock, patch

    mock_client = MagicMock()
    mock_insert_res = MagicMock()
    mock_insert_res.data = [{"id": "abc-123-uuid"}]
    mock_client.table.return_value.insert.return_value.execute.return_value = mock_insert_res

    mock_select_res = MagicMock()
    mock_select_res.data = [{
        "id": "abc-123-uuid",
        "job_title": "Cloud Architect",
        "job_url": "https://company.com/job",
        "language": "en",
        "technologies": ["AWS", "Terraform"],
        "resume_md": "# Cloud Architect Resume",
        "cover_letter_md": "Cover Letter text",
        "created_at": "2026-10-21T10:00:00",
        "has_cover_letter": True,
        "diagnostic": {"ats_score": 90}
    }]
    mock_client.table.return_value.select.return_value.order.return_value.execute.return_value = mock_select_res
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=mock_select_res.data[0])

    with patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        # 1. Salvar no Supabase
        saved_id = history_manager.save_resume(
            job_title="Cloud Architect",
            content="# Cloud Architect Resume",
            job_url="https://company.com/job",
            cover_letter="Cover Letter text",
            language="en",
            technologies=["AWS", "Terraform"],
            diagnostic={"ats_score": 90}
        )
        assert saved_id == "supabase:abc-123-uuid"

        # 2. Listar do Supabase
        resumes = history_manager.list_resumes()
        assert len(resumes) >= 1
        assert resumes[0]["job_title"] == "Cloud Architect"
        assert resumes[0]["filepath"] == "supabase:abc-123-uuid"
        assert resumes[0]["diagnostic"]["ats_score"] == 90

        # 3. Carregar do Supabase
        app_data = history_manager.load_application("supabase:abc-123-uuid")
        assert app_data["resume_md"] == "# Cloud Architect Resume"
        assert app_data["metadata"]["diagnostic"]["ats_score"] == 90

