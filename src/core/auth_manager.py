import json
import hmac
import time
import hashlib
import base64
from typing import Dict, Any, Optional
from src.core import config, history_manager

GUEST_USER_ID = "guest_local"
# Mesma validade do max-age do cookie de sessão
SESSION_TTL_SECONDS = 30 * 24 * 3600

def _secret() -> bytes:
    if not config.AUTH_SECRET_KEY:
        raise RuntimeError(
            "AUTH_SECRET_KEY não configurada. Gere uma com "
            "`python -c \"import secrets; print(secrets.token_urlsafe(48))\"` e defina no .env."
        )
    return config.AUTH_SECRET_KEY.encode("utf-8")

def _user(user_id: str, email: str, display_name: str) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "is_authenticated": True,
        "is_guest": False
    }

def create_guest_session() -> Dict[str, Any]:
    """Cria uma sessão de convidado/visitante para uso anônimo e local."""
    return {
        "user_id": GUEST_USER_ID,
        "email": "visitante@local",
        "display_name": "Visitante Convidado",
        "is_authenticated": True,
        "is_guest": True
    }

def create_session_token(user: Dict[str, Any]) -> str:
    """
    Gera o token do cookie de sessão (sobrevive ao F5), assinado por HMAC-SHA256 e com expiração.
    Não carrega tokens do provedor de autenticação.
    """
    payload = {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "exp": int(time.time()) + SESSION_TTL_SECONDS
    }
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = hmac.new(_secret(), raw, hashlib.sha256).hexdigest()
    return f"{base64.urlsafe_b64encode(raw).decode('utf-8')}.{sig}"

def restore_session_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida assinatura e expiração do token e restaura a sessão autenticada do usuário.
    Retorna None se o token for inválido, adulterado ou expirado.
    """
    if not token or "." not in token:
        return None
    secret = _secret()  # fora do try: segredo ausente é erro de configuração, não token inválido
    try:
        raw_b64, sig = token.split(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64.encode('utf-8'))
        if not hmac.compare_digest(sig, hmac.new(secret, raw, hashlib.sha256).hexdigest()):
            return None
        payload = json.loads(raw.decode('utf-8'))
    except Exception:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    if not payload.get("user_id") or payload.get("user_id") == GUEST_USER_ID:
        return None
    return _user(payload["user_id"], payload.get("email", ""), payload.get("display_name", ""))

def _local_user(email: str, display_name: str) -> Dict[str, Any]:
    # ponytail: modo local de desenvolvimento sem verificação de senha; use Supabase em qualquer deploy
    user_id = "local-" + hashlib.sha256(email.lower().encode('utf-8')).hexdigest()[:16]
    return _user(user_id, email, display_name)

def _auth_client():
    """
    Cliente anon novo a cada chamada: o login muda o estado de autenticação do cliente,
    então ele nunca é compartilhado entre sessões nem usado para dados.
    """
    from supabase import create_client, ClientOptions
    return create_client(
        history_manager.supabase_url(),
        config.SUPABASE_KEY,
        ClientOptions(auto_refresh_token=False, persist_session=False)
    )

def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    """
    Realiza a autenticação com e-mail e senha no Supabase Auth.
    Se o Supabase não estiver configurado, permite login em ambiente local.
    """
    clean_email = email.strip()
    if not clean_email or not password:
        return {
            "success": False,
            "user": None,
            "error": "Por favor, informe e-mail e senha."
        }

    if not history_manager.is_supabase_configured():
        return {
            "success": True,
            "user": _local_user(clean_email, clean_email.split("@")[0].capitalize()),
            "error": None
        }

    try:
        res = _auth_client().auth.sign_in_with_password({
            "email": clean_email,
            "password": password
        })
        if res.user:
            return {
                "success": True,
                "user": _user(
                    str(res.user.id),
                    res.user.email or clean_email,
                    (res.user.user_metadata or {}).get("full_name") or clean_email.split("@")[0].capitalize()
                ),
                "error": None
            }
        return {
            "success": False,
            "user": None,
            "error": "Não foi possível validar as credenciais."
        }
    except Exception as e:
        err_msg = str(e)
        if "Invalid login credentials" in err_msg:
            err_msg = "E-mail ou senha incorretos."
        elif "Email not confirmed" in err_msg:
            err_msg = "E-mail ainda não confirmado. Verifique sua caixa de entrada."
        return {
            "success": False,
            "user": None,
            "error": err_msg
        }

def sign_up(email: str, password: str, full_name: str = "") -> Dict[str, Any]:
    """
    Cria uma nova conta de usuário no Supabase Auth.
    """
    clean_email = email.strip()
    clean_name = full_name.strip()
    if not clean_email or not password:
        return {
            "success": False,
            "user": None,
            "error": "Por favor, informe e-mail e senha válidos."
        }
    if len(password) < 6:
        return {
            "success": False,
            "user": None,
            "error": "A senha deve ter no mínimo 6 caracteres."
        }

    if not history_manager.is_supabase_configured():
        return {
            "success": True,
            "user": _local_user(clean_email, clean_name or clean_email.split("@")[0].capitalize()),
            "error": None,
            "message": "Conta local criada com sucesso!"
        }

    try:
        signup_options = {}
        if clean_name:
            signup_options["data"] = {"full_name": clean_name}

        res = _auth_client().auth.sign_up({
            "email": clean_email,
            "password": password,
            "options": signup_options
        })
        if res.user:
            return {
                "success": True,
                "user": _user(str(res.user.id), res.user.email or clean_email, clean_name or clean_email.split("@")[0].capitalize()),
                "error": None,
                "message": "Conta criada com sucesso!"
            }
        return {
            "success": False,
            "user": None,
            "error": "Não foi possível criar o usuário."
        }
    except Exception as e:
        err_msg = str(e)
        if "User already registered" in err_msg:
            err_msg = "Este e-mail já está cadastrado. Faça login ou use outro e-mail."
        return {
            "success": False,
            "user": None,
            "error": err_msg
        }
