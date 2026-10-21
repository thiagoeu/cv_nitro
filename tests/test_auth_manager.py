from unittest.mock import MagicMock, patch
from src.core import auth_manager

def test_guest_session_creation():
    session = auth_manager.create_guest_session()
    assert session["user_id"] == "guest_local"
    assert session["is_authenticated"] is True
    assert session["is_guest"] is True
    assert "visitante" in session["email"]

def test_local_dev_sign_in(monkeypatch):
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: False)
    res = auth_manager.sign_in_with_password("user@test.com", "password123")
    assert res["success"] is True
    assert res["user"]["email"] == "user@test.com"
    assert res["user"]["is_authenticated"] is True
    assert res["user"]["is_guest"] is False

def test_sign_in_validation_empty_fields():
    res = auth_manager.sign_in_with_password("", "")
    assert res["success"] is False
    assert "informe e-mail e senha" in res["error"].lower()

def test_sign_up_short_password():
    res = auth_manager.sign_up("user@test.com", "123")
    assert res["success"] is False
    assert "mínimo 6 caracteres" in res["error"]

def test_supabase_sign_in_mocked_success():
    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user-uuid-1234"
    mock_user.email = "candidato@empresa.com"
    mock_user.user_metadata = {"full_name": "Candidato Silva"}
    
    mock_session = MagicMock()
    mock_session.access_token = "valid-jwt-token"
    
    mock_auth_res = MagicMock(user=mock_user, session=mock_session)
    mock_client.auth.sign_in_with_password.return_value = mock_auth_res
    
    with patch("src.core.history_manager.is_supabase_configured", return_value=True), \
         patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        res = auth_manager.sign_in_with_password("candidato@empresa.com", "senhaForte123")
        assert res["success"] is True
        assert res["user"]["user_id"] == "user-uuid-1234"
        assert res["user"]["display_name"] == "Candidato Silva"
        assert res["user"]["access_token"] == "valid-jwt-token"

def test_supabase_sign_in_mocked_invalid_credentials():
    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
    
    with patch("src.core.history_manager.is_supabase_configured", return_value=True), \
         patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        res = auth_manager.sign_in_with_password("errado@empresa.com", "senhaErrada")
        assert res["success"] is False
        assert "E-mail ou senha incorretos" in res["error"]

def test_sign_out_executes():
    mock_client = MagicMock()
    with patch("src.core.history_manager.is_supabase_configured", return_value=True), \
         patch("src.core.history_manager.get_supabase_client", return_value=mock_client):
        ok = auth_manager.sign_out()
        assert ok is True
        assert mock_client.auth.sign_out.called
