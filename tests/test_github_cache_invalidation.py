import pytest
from unittest.mock import patch, MagicMock
from src.agents.nodes.github import github_fetcher, check_github_staleness
from src.ui.wizard_view import build_initial_state
from src.core import profile_manager


def test_github_fetcher_reuses_cache_when_force_refresh_false():
    cached = [{"name": "repo1", "html_url": "https://github.com/octocat/repo1"}]
    state = {
        "github_username": "octocat",
        "raw_github_repos": cached,
        "force_github_refresh": False
    }
    with patch("requests.get") as mock_get:
        res = github_fetcher(state)
        assert not mock_get.called
    assert res["raw_github_repos"] == cached
    assert "Reaproveitados 1 repositórios do cache" in res["agent_trace"][0]["detail"]


def test_github_fetcher_bypasses_cache_when_force_refresh_true():
    cached = [{"name": "repo1", "html_url": "https://github.com/octocat/repo1"}]
    fresh_repos = [
        {"name": "repo1", "fork": False, "html_url": "https://github.com/octocat/repo1"},
        {"name": "repo2-novo", "fork": False, "html_url": "https://github.com/octocat/repo2-novo"}
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fresh_repos

    state = {
        "github_username": "octocat",
        "raw_github_repos": cached,
        "force_github_refresh": True
    }
    with patch("requests.get", return_value=mock_resp) as mock_get:
        res = github_fetcher(state)
        assert mock_get.called
    assert len(res["raw_github_repos"]) == 2
    assert res["raw_github_repos"][1]["name"] == "repo2-novo"
    assert "atualização forçada sob demanda" in res["agent_trace"][0]["detail"]


def test_profile_manager_records_github_synced_at(tmp_path, monkeypatch):
    test_dir = str(tmp_path / "profiles")
    monkeypatch.setenv("PROFILES_DIR", test_dir)
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: False)

    user_id = "user-test-cache-sync"
    repos = [
        {
            "name": "novo-projeto",
            "description": "Descricao do projeto",
            "language": "Python",
            "topics": ["ai", "agents"],
            "stargazers_count": 10,
            "fork": False,
            "updated_at": "2026-11-13T10:00:00Z",
            "html_url": "https://github.com/thiagoeu/novo-projeto",
            "default_branch": "main"
        }
    ]

    ok = profile_manager.update_cached_github_repos(user_id, repos)
    assert ok is True

    prof = profile_manager.get_user_profile(user_id)
    assert len(prof["cached_repos"]) == 1
    assert prof["cached_repos"][0]["name"] == "novo-projeto"
    assert "github_synced_at" in prof
    assert prof["github_synced_at"] != ""


def test_check_github_staleness_detected():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"public_repos": 19}

    with patch("requests.get", return_value=mock_resp):
        result = check_github_staleness("thiagoeu", cached_count=18)

    assert result["stale"] is True
    assert result["remote_count"] == 19
    assert result["cached_count"] == 18
    assert result["difference"] == 1


def test_check_github_staleness_not_stale():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"public_repos": 18}

    with patch("requests.get", return_value=mock_resp):
        result = check_github_staleness("thiagoeu", cached_count=18)

    assert result["stale"] is False
    assert result["remote_count"] == 18
    assert result["difference"] == 0


def test_check_github_staleness_api_error_handled():
    mock_resp = MagicMock()
    mock_resp.status_code = 403

    with patch("requests.get", return_value=mock_resp):
        result = check_github_staleness("thiagoeu", cached_count=18)

    assert result["stale"] is False
    assert result["remote_count"] is None
    assert "error" in result


def test_build_initial_state_respects_force_github_refresh():
    profile = {
        "github_username": "thiagoeu",
        "cached_repos": [{"name": "repo1", "html_url": "https://github.com/thiagoeu/repo1"}]
    }

    # Sem force_refresh: reaproveita cache
    state_cached = build_initial_state(
        job_description="Vaga Python",
        base_resume="CV",
        github_username="thiagoeu",
        job_url="https://vaga.com",
        generate_cover_letter=False,
        strict_review=False,
        profile=profile,
        force_github_refresh=False
    )
    assert state_cached.get("raw_github_repos") is not None
    assert len(state_cached["raw_github_repos"]) == 1

    # Com force_refresh: nao injeta cache no estado inicial
    state_refresh = build_initial_state(
        job_description="Vaga Python",
        base_resume="CV",
        github_username="thiagoeu",
        job_url="https://vaga.com",
        generate_cover_letter=False,
        strict_review=False,
        profile=profile,
        force_github_refresh=True
    )
    assert state_refresh.get("raw_github_repos") is None
    assert state_refresh.get("force_github_refresh") is True
