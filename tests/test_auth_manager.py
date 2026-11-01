import json
import base64
import pytest
from unittest.mock import MagicMock, patch
from src.core import auth_manager

def _supabase_mode(monkeypatch):
    monkeypatch.setattr("src.core.history_manager.is_supabase_configured", lambda: True)
    monkeypatch.setattr("src.core.config.SUPABASE_URL", "https://proj.supabase.co")
    monkeypatch.setattr("src.core.config.SUPABASE_KEY", "anon-key")

def test_guest_session_creation():
    session = auth_manager.create_guest_session()
    assert session["user_id"] == "guest_local"
    assert session["is_authenticated"] is True
    assert session["is_guest"] is True
    assert "visitante" in session["email"]

def test_local_dev_sign_in():
    res = auth_manager.sign_in_with_password("user@test.com", "password123")
    assert res["success"] is True
    assert res["user"]["email"] == "user@test.com"
    assert res["user"]["is_authenticated"] is True
    assert res["user"]["is_guest"] is False

def test_local_dev_user_id_per_email():
    a = auth_manager.sign_in_with_password("ana@test.com", "x")["user"]["user_id"]
    a_again = auth_manager.sign_up("ANA@test.com", "123456")["user"]["user_id"]
    b = auth_manager.sign_in_with_password("bia@test.com", "x")["user"]["user_id"]
    assert a.startswith("local-")
    assert a == a_again
    assert a != b

def test_sign_in_validation_empty_fields():
    res = auth_manager.sign_in_with_password("", "")
    assert res["success"] is False
    assert "informe e-mail e senha" in res["error"].lower()

def test_sign_up_short_password():
    res = auth_manager.sign_up("user@test.com", "123")
    assert res["success"] is False
    assert "mínimo 6 caracteres" in res["error"]

def test_supabase_sign_in_mocked_success(monkeypatch):
    _supabase_mode(monkeypatch)
    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user-uuid-1234"
    mock_user.email = "candidato@empresa.com"
    mock_user.user_metadata = {"full_name": "Candidato Silva"}
    mock_client.auth.sign_in_with_password.return_value = MagicMock(user=mock_user, session=MagicMock())

    with patch("src.core.auth_manager._auth_client", return_value=mock_client):
        res = auth_manager.sign_in_with_password("candidato@empresa.com", "senhaForte123")
    assert res["success"] is True
    assert res["user"]["user_id"] == "user-uuid-1234"
    assert res["user"]["display_name"] == "Candidato Silva"
    assert "access_token" not in res["user"]

def test_supabase_sign_in_mocked_invalid_credentials(monkeypatch):
    _supabase_mode(monkeypatch)
    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    with patch("src.core.auth_manager._auth_client", return_value=mock_client):
        res = auth_manager.sign_in_with_password("errado@empresa.com", "senhaErrada")
    assert res["success"] is False
    assert "E-mail ou senha incorretos" in res["error"]

def test_auth_uses_fresh_anon_client_per_call(monkeypatch):
    _supabase_mode(monkeypatch)
    created = []
    def fake_create_client(url, key, options=None):
        client = MagicMock()
        client.auth.sign_in_with_password.return_value = MagicMock(user=MagicMock(id="u1", email="a@b.com", user_metadata={}))
        created.append((url, key, options))
        return client

    with patch("supabase.create_client", side_effect=fake_create_client), \
         patch("src.core.history_manager.get_supabase_client") as data_client:
        auth_manager.sign_in_with_password("a@b.com", "senha123")
        auth_manager.sign_in_with_password("a@b.com", "senha123")
        auth_manager.sign_up("c@d.com", "senha123")

    assert len(created) == 3
    assert all(key == "anon-key" for _, key, _ in created)
    # Sem auto-refresh: o timer do supabase-py manteria o cliente descartável vivo
    assert all(opts.auto_refresh_token is False and opts.persist_session is False for _, _, opts in created)
    assert not data_client.called

def test_session_token_create_and_restore_success():
    user = {"user_id": "usr-test-1234", "email": "thiago@exemplo.com", "display_name": "Thiago Araujo"}
    token = auth_manager.create_session_token(user)
    restored = auth_manager.restore_session_from_token(token)
    assert restored == {
        "user_id": "usr-test-1234",
        "email": "thiago@exemplo.com",
        "display_name": "Thiago Araujo",
        "is_authenticated": True,
        "is_guest": False
    }

def test_session_token_payload_has_exp_and_no_provider_token():
    user = {"user_id": "u-1", "email": "a@b.com", "display_name": "A", "access_token": "jwt-do-provedor"}
    token = auth_manager.create_session_token(user)
    payload = json.loads(base64.urlsafe_b64decode(token.split(".", 1)[0]))
    assert set(payload) == {"user_id", "email", "display_name", "exp"}
    assert "jwt-do-provedor" not in token

def test_session_token_expired_rejected(monkeypatch):
    token = auth_manager.create_session_token({"user_id": "u-1", "email": "a@b.com", "display_name": "A"})
    now = auth_manager.time.time()
    monkeypatch.setattr(auth_manager.time, "time", lambda: now + auth_manager.SESSION_TTL_SECONDS + 1)
    assert auth_manager.restore_session_from_token(token) is None

def test_session_token_tampered_rejected():
    token = auth_manager.create_session_token({"user_id": "usr-test-5678", "email": "h@t.com", "display_name": "H"})
    raw, sig = token.split(".", 1)
    assert auth_manager.restore_session_from_token(f"{raw}.{'a' * len(sig)}") is None
    # Payload trocado mantendo a assinatura original
    forged = base64.urlsafe_b64encode(json.dumps({"user_id": "outro", "exp": 9999999999}).encode()).decode()
    assert auth_manager.restore_session_from_token(f"{forged}.{sig}") is None

def test_session_token_empty_or_guest_rejected():
    assert auth_manager.restore_session_from_token("") is None
    assert auth_manager.restore_session_from_token(None) is None
    assert auth_manager.restore_session_from_token("invalid_token_without_dot") is None
    guest_token = auth_manager.create_session_token({"user_id": "guest_local", "email": "visitante@local"})
    assert auth_manager.restore_session_from_token(guest_token) is None

def test_session_token_requires_secret(monkeypatch):
    token = auth_manager.create_session_token({"user_id": "u-1", "email": "a@b.com", "display_name": "A"})
    monkeypatch.setattr("src.core.config.AUTH_SECRET_KEY", None)
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        auth_manager.create_session_token({"user_id": "u-1"})
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        auth_manager.restore_session_from_token(token)

def test_session_token_url_encoded_and_unicode():
    import urllib.parse
    user = {
        "user_id": "uuid-thiago-2026",
        "email": "barbosa.araujo@academico.ifpb.edu.br",
        "display_name": "Thiago Barbosa de Araújo"
    }
    token = auth_manager.create_session_token(user)
    # Simula como o cookie armazena (com encodeURIComponent / quote e aspas)
    encoded_cookie = f'"{urllib.parse.quote(token)}"'
    restored = auth_manager.restore_session_from_token(urllib.parse.unquote(encoded_cookie.strip('"')))
    assert restored["user_id"] == "uuid-thiago-2026"
    assert restored["display_name"] == "Thiago Barbosa de Araújo"
    assert restored["is_guest"] is False

def _restore_with_cookie(cookie_token):
    import app
    import streamlit as st
    fake_context = MagicMock()
    fake_context.cookies = {"cv_nitro_auth_token": cookie_token} if cookie_token else {}
    with patch.object(app.st, "context", fake_context):
        app.restore_session()
    return st.session_state.user_session

def test_app_ignores_session_token_in_url():
    import streamlit as st
    st.session_state.clear()
    st.query_params["auth_token"] = auth_manager.create_session_token({"user_id": "u-url", "email": "a@b.com", "display_name": "A"})
    try:
        assert _restore_with_cookie(None)["is_guest"] is True
    finally:
        st.query_params.clear()

def test_app_restores_session_from_cookie():
    import streamlit as st
    st.session_state.clear()
    token = auth_manager.create_session_token({"user_id": "u-cookie", "email": "a@b.com", "display_name": "A"})
    assert _restore_with_cookie(token)["user_id"] == "u-cookie"

def test_app_logout_not_undone_by_stale_cookie():
    import streamlit as st
    st.session_state.clear()
    token = auth_manager.create_session_token({"user_id": "u-cookie", "email": "a@b.com", "display_name": "A"})
    st.session_state["logged_out"] = True
    # Reruns seguintes ao logout ainda veem o cookie da requisição inicial
    assert _restore_with_cookie(token)["is_guest"] is True
    assert _restore_with_cookie(token)["is_guest"] is True
