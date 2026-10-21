from src.core import db_migrator
from unittest.mock import patch, MagicMock

def test_db_migrator_local_mode(monkeypatch):
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: False)
    status = db_migrator.check_or_setup_tables()
    assert status["supabase_connected"] is False
    assert status["local_ready"] is True
    assert "local" in status["message"].lower()

def test_db_migrator_supabase_mocked():
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    
    with patch("src.core.history_manager.is_supabase_configured", return_value=True), \
         patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        status = db_migrator.check_or_setup_tables()
        assert status["supabase_connected"] is True
        assert status["applications_ready"] is True
        assert status["user_profiles_ready"] is True
