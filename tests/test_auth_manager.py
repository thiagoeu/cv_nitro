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

def test_session_token_create_and_restore_success():
    user = {
        "user_id": "usr-test-1234",
        "email": "thiago@exemplo.com",
        "display_name": "Thiago Araujo",
        "access_token": "token-xyz"
    }
    token = auth_manager.create_session_token(user)
    assert isinstance(token, str)
    assert "." in token

    restored = auth_manager.restore_session_from_token(token)
    assert restored is not None
    assert restored["user_id"] == "usr-test-1234"
    assert restored["email"] == "thiago@exemplo.com"
    assert restored["display_name"] == "Thiago Araujo"
    assert restored["is_authenticated"] is True
    assert restored["is_guest"] is False
    assert restored["access_token"] == "token-xyz"

def test_session_token_tampered_rejected():
    user = {
        "user_id": "usr-test-5678",
        "email": "hacker@teste.com",
        "display_name": "Hacker",
        "access_token": "abc"
    }
    token = auth_manager.create_session_token(user)
    raw, sig = token.split(".", 1)
    tampered_sig = "a" * len(sig)
    tampered_token = f"{raw}.{tampered_sig}"
    assert auth_manager.restore_session_from_token(tampered_token) is None

def test_session_token_empty_or_guest_rejected():
    assert auth_manager.restore_session_from_token("") is None
    assert auth_manager.restore_session_from_token(None) is None
    assert auth_manager.restore_session_from_token("invalid_token_without_dot") is None
    
    guest_user = {"user_id": "guest_local", "email": "visitante@local"}
    guest_token = auth_manager.create_session_token(guest_user)
    assert auth_manager.restore_session_from_token(guest_token) is None
