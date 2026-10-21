import os
from unittest.mock import MagicMock, patch
from src.core import profile_manager

def test_default_profile_structure():
    prof = profile_manager.get_default_profile("test-uuid", "test@test.com")
    assert prof["user_id"] == "test-uuid"
    assert prof["email"] == "test@test.com"
    assert prof["base_resume"] == ""
    assert isinstance(prof["cached_repos"], list)

def test_local_profile_persistence(tmp_path, monkeypatch):
    test_profiles_dir = str(tmp_path / "profiles")
    monkeypatch.setenv("PROFILES_DIR", test_profiles_dir)
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: False)

    # 1. Salvar perfil com currículo base e GitHub
    profile_data = {
        "email": "candidato@test.com",
        "full_name": "Thiago Araújo",
        "base_resume": "# Thiago Araújo\nDesenvolvedor Full Stack",
        "github_username": "thiagoeu",
        "skills": ["Python", "FastAPI", "React"],
        "cached_repos": [
            {"name": "repo-context", "description": "RAG engine", "stars": 12}
        ]
    }
    saved = profile_manager.save_user_profile("user-123", profile_data)
    assert saved is True

    # 2. Recuperar perfil
    loaded = profile_manager.get_user_profile("user-123")
    assert loaded["user_id"] == "user-123"
    assert loaded["full_name"] == "Thiago Araújo"
    assert "Desenvolvedor Full Stack" in loaded["base_resume"]
    assert loaded["github_username"] == "thiagoeu"
    assert len(loaded["cached_repos"]) == 1
    assert loaded["cached_repos"][0]["name"] == "repo-context"

    # 3. Atualizar cache de repositórios do GitHub
    new_repos = [
        {"name": "repo-context", "description": "RAG engine", "stars": 12},
        {"name": "MicroServicesSales", "description": "NestJS Saga", "stars": 5}
    ]
    profile_manager.update_cached_github_repos("user-123", new_repos)
    cached = profile_manager.get_cached_github_repos("user-123")
    assert len(cached) == 2
    assert cached[1]["name"] == "MicroServicesSales"

def test_supabase_profile_mocked():
    mock_client = MagicMock()
    mock_data = [{
        "user_id": "supa-user-999",
        "email": "supa@dev.com",
        "full_name": "Dev Supabase",
        "base_resume": "# Base CV Supabase",
        "github_username": "octocat",
        "cached_repos": [{"name": "hello-world"}],
        "skills": ["SQL", "Postgres"],
        "updated_at": "2026-10-21T10:00:00"
    }]
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=mock_data)

    with patch("src.core.history_manager.is_supabase_configured", return_value=True), \
         patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        prof = profile_manager.get_user_profile("supa-user-999")
        assert prof["full_name"] == "Dev Supabase"
        assert prof["github_username"] == "octocat"
        assert len(prof["cached_repos"]) == 1
