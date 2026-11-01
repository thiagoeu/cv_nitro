import os
import json
from datetime import datetime
from src.core import history_manager

UID = "user-aaa-111"
OTHER = "user-bbb-222"

def _write_local(name: str, metadata: dict, body: str = "# CV") -> str:
    path = os.path.join(history_manager.get_history_dir(), name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!--\n{json.dumps(metadata)}\n-->\n\n{body}")
    return path

def test_history_manager():
    filepath = history_manager.save_resume(
        job_title="Senior Python Engineer",
        content="# My Resume\nPython, AI, Cloud.",
        job_url="https://linkedin.com/jobs/view/9999",
        cover_letter="Dear Team,\n\nI love this role.",
        language="en",
        technologies=["Python", "LangGraph"],
        user_id=UID
    )
    assert os.path.exists(filepath)

    resumes = history_manager.list_resumes(UID)
    assert resumes[0]["job_title"] == "Senior Python Engineer"
    assert resumes[0]["job_url"] == "https://linkedin.com/jobs/view/9999"
    assert resumes[0]["language"] == "en"

    app_data = history_manager.load_application(resumes[0]["filepath"], UID)
    assert app_data["resume_md"].startswith("# My Resume")
    assert "Dear Team" not in app_data["resume_md"]
    assert "Dear Team" in app_data["cover_letter_md"]
    assert app_data["metadata"]["job_url"] == "https://linkedin.com/jobs/view/9999"

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
        github_username="thiagoeu",
        user_id=UID
    )

    app_data = history_manager.load_application(filepath, UID)
    assert app_data["metadata"]["job_description"] == "Job description details..."
    assert app_data["metadata"]["base_resume"] == "# Base Resume Text"
    assert app_data["metadata"]["github_username"] == "thiagoeu"

    updated_filepath = history_manager.save_resume(
        job_title="Full Stack Engineer",
        content="# Updated Optimized Resume",
        job_url="https://example.com/job/1",
        cover_letter="Updated Letter",
        filepath=filepath,
        diagnostic={"ats_score": 95},
        user_id=UID
    )
    assert updated_filepath == filepath
    updated_app = history_manager.load_application(filepath, UID)
    assert updated_app["resume_md"] == "# Updated Optimized Resume"
    assert updated_app["cover_letter_md"] == "Updated Letter"
    assert updated_app["metadata"]["diagnostic"]["ats_score"] == 95

def test_missing_supabase_settings(monkeypatch):
    for name, value in (("SUPABASE_URL", "https://proj.supabase.co"), ("SUPABASE_KEY", "anon"), ("SUPABASE_SERVICE_ROLE_KEY", "service")):
        monkeypatch.setattr(f"src.core.config.{name}", value)
    assert history_manager.missing_supabase_settings() == []

    monkeypatch.setattr("src.core.config.SUPABASE_SERVICE_ROLE_KEY", None)
    assert history_manager.missing_supabase_settings() == ["SUPABASE_SERVICE_ROLE_KEY"]

    monkeypatch.setattr("src.core.config.SUPABASE_URL", "https://your-project.supabase.co")
    monkeypatch.setattr("src.core.config.SUPABASE_KEY", "")
    assert history_manager.missing_supabase_settings() == ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY"]

def test_supabase_operations(fake_supabase):
    saved_id = history_manager.save_resume(
        job_title="Cloud Architect",
        content="# Cloud Architect Resume",
        job_url="https://company.com/job",
        cover_letter="Cover Letter text",
        language="en",
        technologies=["AWS", "Terraform"],
        diagnostic={"ats_score": 90},
        user_id=UID
    )
    assert saved_id == "supabase:id-1"
    assert fake_supabase.tables["applications"][0]["user_id"] == UID

    resumes = history_manager.list_resumes(UID)
    assert [r["filepath"] for r in resumes] == ["supabase:id-1"]  # cópia local não duplica
    assert resumes[0]["diagnostic"]["ats_score"] == 90
    list_query = next(q for q in fake_supabase.calls if q.op == "select")
    assert list_query.payload == history_manager.LIST_COLUMNS

    app_data = history_manager.load_application("supabase:id-1", UID)
    assert app_data["resume_md"] == "# Cloud Architect Resume"
    assert app_data["metadata"]["diagnostic"]["ats_score"] == 90

def test_every_db_operation_filters_owner(fake_supabase):
    path = history_manager.save_resume(job_title="Vaga", content="# CV", user_id=UID)
    history_manager.save_resume(job_title="Vaga", content="# CV v2", filepath=path, user_id=UID)
    history_manager.list_resumes(UID)
    history_manager.load_application(path, UID)
    history_manager.delete_application(path, UID)

    ops = {q.op for q in fake_supabase.calls}
    assert {"insert", "update", "select", "delete"} <= ops
    for q in fake_supabase.calls:
        if q.op == "insert":
            assert q.payload["user_id"] == UID
        else:
            assert ("user_id", UID) in q.filters, f"{q.op} sem filtro de dono"

def test_other_user_cannot_load_or_delete(fake_supabase):
    path = history_manager.save_resume(job_title="Vaga de A", content="# CV A", user_id=UID)
    local_copy = history_manager._local_copy_of(path[len("supabase:"):])

    assert history_manager.load_application(path, OTHER)["resume_md"] == ""
    assert history_manager.load_application(local_copy, OTHER)["resume_md"] == ""
    assert history_manager.delete_application(path, OTHER) is False
    assert history_manager.delete_application(local_copy, OTHER) is False
    assert len(fake_supabase.tables["applications"]) == 1
    assert os.path.exists(local_copy)

def test_guest_never_reaches_database(fake_supabase):
    history_manager.save_resume(job_title="Vaga", content="# CV", user_id="guest_local")
    history_manager.list_resumes("guest_local")
    assert fake_supabase.calls == []

def test_cloud_failure_returns_local_path(fake_supabase):
    fake_supabase.fail = True
    path = history_manager.save_resume(job_title="Vaga", content="# CV", user_id=UID)
    assert not path.startswith("supabase:")
    assert os.path.exists(path)

def test_repeated_cloud_edits_keep_single_copy(fake_supabase):
    path = history_manager.save_resume(job_title="Vaga", content="# CV", user_id=UID)
    for i in range(3):
        assert history_manager.save_resume(job_title="Vaga", content=f"# CV v{i}", filepath=path, user_id=UID) == path
    assert len(fake_supabase.tables["applications"]) == 1
    assert len(os.listdir(history_manager.get_history_dir())) == 1
    assert history_manager.load_application(path, UID)["resume_md"] == "# CV v2"

def test_edit_preserves_creation_date_and_order():
    old = _write_local("old.md", {"job_title": "Antiga", "date": "2026-01-01T10:00:00-03:00", "user_id": UID})
    history_manager.save_resume(job_title="Recente", content="# CV", user_id=UID)

    history_manager.save_resume(job_title="Antiga", content="# CV editado", filepath=old, user_id=UID)

    assert history_manager.load_application(old, UID)["metadata"]["date"] == "2026-01-01T10:00:00-03:00"
    assert [r["job_title"] for r in history_manager.list_resumes(UID)] == ["Recente", "Antiga"]

def test_dates_displayed_in_local_timezone():
    utc_value = "2026-10-25T11:03:06.12345+00:00"
    expected = datetime.fromisoformat(utc_value).astimezone().strftime("%d/%m/%Y %H:%M")
    assert history_manager.format_display_date(utc_value) == expected
    # Mesmo instante gravado com offset local e em UTC exibe a mesma hora
    local_value = datetime.fromisoformat(utc_value).astimezone().isoformat()
    assert history_manager.format_display_date(local_value) == expected
    assert history_manager.format_display_date("20261025_080306") == "25/10/2026 08:03"

def test_local_listing_excludes_ownerless_and_other_users():
    _write_local("sem_dono.md", {"job_title": "Sem dono", "date": "2026-10-01T10:00:00"})
    _write_local("de_outro.md", {"job_title": "De outro", "date": "2026-10-01T10:00:00", "user_id": OTHER})
    history_manager.save_resume(job_title="Minha", content="# CV", user_id=UID)
    assert [r["job_title"] for r in history_manager.list_resumes(UID)] == ["Minha"]

def test_sync_uploads_only_current_user_files(fake_supabase):
    _write_local("a.md", {"job_title": "Vaga A", "date": "2026-10-01T10:00:00", "user_id": UID})
    _write_local("b.md", {"job_title": "Vaga B", "date": "2026-10-01T10:00:00", "user_id": OTHER})
    _write_local("sem.md", {"job_title": "Sem dono", "date": "2026-10-01T10:00:00"})

    assert history_manager.sync_local_to_supabase(UID) == 1
    rows = fake_supabase.tables["applications"]
    assert [(r["job_title"], r["user_id"]) for r in rows] == [("Vaga A", UID)]
    # Já sincronizado: não envia de novo
    assert history_manager.sync_local_to_supabase(UID) == 0

def test_chronological_ordering():
    history_manager.save_resume(job_title="Oldest Job", content="Old", user_id=UID)
    _write_local("older.md", {"job_title": "Very Old Job", "date": "2025-01-01T10:00:00", "user_id": UID})
    history_manager.save_resume(job_title="Newest Job", content="New", user_id=UID)
    titles = [r["job_title"] for r in history_manager.list_resumes(UID)]
    assert titles[-1] == "Very Old Job"
    assert set(titles[:2]) == {"Oldest Job", "Newest Job"}

def test_delete_application():
    f = history_manager.save_resume(job_title="To Delete", content="Del", user_id=UID)
    assert any(r["job_title"] == "To Delete" for r in history_manager.list_resumes(UID))
    assert history_manager.delete_application(f, UID) is True
    assert not any(r["job_title"] == "To Delete" for r in history_manager.list_resumes(UID))

def test_user_id_isolation():
    history_manager.save_resume(job_title="Dev Python para User A", content="Resume A", user_id=UID)
    history_manager.save_resume(job_title="Dev React para User B", content="Resume B", user_id=OTHER)
    assert [r["job_title"] for r in history_manager.list_resumes(UID)] == ["Dev Python para User A"]
    assert [r["job_title"] for r in history_manager.list_resumes(OTHER)] == ["Dev React para User B"]
