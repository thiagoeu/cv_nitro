import os
import io
from src.core.document_parser import extract_text_from_file
from src.core import history_manager

def test_full_pipeline_mock():
    # 1. Simula arquivo PDF/Markdown enviado pelo usuário
    mock_resume_md = (
        "# John Doe\n\n"
        "## Summary\nSenior Software Engineer with 6+ years in Python, Cloud, and Multi-Agent systems.\n\n"
        "## Experience\n- Lead Developer at TechCorp: Built scalable LangGraph multi-agent systems.\n"
    )
    stream = io.BytesIO(mock_resume_md.encode("utf-8"))
    stream.name = "john_doe_resume.md"
    extracted_text = extract_text_from_file(stream)
    assert "John Doe" in extracted_text
    assert "LangGraph" in extracted_text

    # 2. Simula dados de vaga em inglês
    job_title = "Staff AI Agent Engineer"
    job_url = "https://careers.google.com/jobs/results/123456"
    job_lang = "en"
    job_techs = ["Python", "LangGraph", "Gemini", "Docker"]
    
    mock_generated_cv = (
        "# John Doe - Staff AI Agent Engineer\n\n"
        "## Professional Summary\nResults-driven engineer specializing in LangGraph agent workflows.\n\n"
        "## Key Projects\n- **CV Nitro**: Multi-agent ATS optimizer.\n"
    )
    
    mock_cover_letter = (
        "Dear Hiring Manager,\n\n"
        "I am writing to express my strong interest in the Staff AI Agent Engineer position. "
        "With my proven track record in Python and multi-agent graph architectures, I look forward "
        "to discussing how I can add immediate value.\n\nSincerely,\nJohn Doe"
    )

    # 3. Salva no histórico com os novos metadados
    saved_file = history_manager.save_resume(
        job_title=job_title,
        content=mock_generated_cv,
        job_url=job_url,
        cover_letter=mock_cover_letter,
        language=job_lang,
        technologies=job_techs
    )
    
    assert os.path.exists(saved_file)
    
    # 4. Carrega e valida persistência para o Dashboard
    app_data = history_manager.load_application(saved_file)
    assert app_data["metadata"]["job_url"] == job_url
    assert app_data["metadata"]["language"] == "en"
    assert "Staff AI Agent Engineer" in app_data["resume_md"]
    assert "Dear Hiring Manager" in app_data["cover_letter_md"]
    
    # 5. Valida que o list_resumes inclui a nova aplicação
    resumes = history_manager.list_resumes()
    matching = [r for r in resumes if r.get("job_url") == job_url]
    assert len(matching) > 0
    assert matching[0]["language"] == "en"
    assert matching[0]["has_cover_letter"] is True

    print("End-to-end integration test passed successfully!")

if __name__ == "__main__":
    test_full_pipeline_mock()
