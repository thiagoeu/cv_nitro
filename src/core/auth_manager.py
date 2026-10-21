import os
import json
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional
from src.core import history_manager

GUEST_USER_ID = "guest_local"
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "cv_nitro_session_secret_signature_key_2026")

def create_guest_session() -> Dict[str, Any]:
    """Cria uma sessão de convidado/visitante para uso anônimo e local."""
    return {
        "user_id": GUEST_USER_ID,
        "email": "visitante@local",
        "display_name": "Visitante Convidado",
        "is_authenticated": True,
        "is_guest": True,
        "access_token": None
    }

def create_session_token(user: Dict[str, Any]) -> str:
    """
    Gera um token seguro assinado por HMAC-SHA256 para persistência no navegador
    (localStorage e URL query params), permitindo sobrevivência ao recarregar a página (F5).
    """
    payload = {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "access_token": user.get("access_token")
    }
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = hmac.new(AUTH_SECRET_KEY.encode('utf-8'), raw, hashlib.sha256).hexdigest()
    raw_b64 = base64.urlsafe_b64encode(raw).decode('utf-8')
    return f"{raw_b64}.{sig}"

def restore_session_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida a assinatura do token e restaura a sessão autenticada do usuário.
    Retorna None se o token for inválido, corrompido ou adulterado.
    """
    if not token or "." not in token:
        return None
    try:
        raw_b64, sig = token.split(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64.encode('utf-8'))
        expected_sig = hmac.new(AUTH_SECRET_KEY.encode('utf-8'), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload = json.loads(raw.decode('utf-8'))
        if not payload.get("user_id") or payload.get("user_id") == GUEST_USER_ID:
            return None
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("email", ""),
            "display_name": payload.get("display_name", ""),
            "is_authenticated": True,
            "is_guest": False,
            "access_token": payload.get("access_token")
        }
    except Exception:
        return None

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
        # Modo de desenvolvimento local sem Supabase
        return {
            "success": True,
            "user": {
                "user_id": "local_dev_user",
                "email": clean_email,
                "display_name": clean_email.split("@")[0].capitalize(),
                "is_authenticated": True,
                "is_guest": False,
                "access_token": "local-dummy-token"
            },
            "error": None
        }

    client = history_manager.get_supabase_client()
    if not client:
        return {
            "success": False,
            "user": None,
            "error": "Cliente Supabase indisponível no momento."
        }

    try:
        res = client.auth.sign_in_with_password({
            "email": clean_email,
            "password": password
        })
        if res.user:
            return {
                "success": True,
                "user": {
                    "user_id": str(res.user.id),
                    "email": res.user.email or clean_email,
                    "display_name": (res.user.user_metadata or {}).get("full_name") or clean_email.split("@")[0].capitalize(),
                    "is_authenticated": True,
                    "is_guest": False,
                    "access_token": res.session.access_token if res.session else None
                },
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
            "user": {
                "user_id": "local_dev_user",
                "email": clean_email,
                "display_name": clean_name or clean_email.split("@")[0].capitalize(),
                "is_authenticated": True,
                "is_guest": False,
                "access_token": "local-dummy-token"
            },
            "error": None,
            "message": "Conta local criada com sucesso!"
        }

    client = history_manager.get_supabase_client()
    if not client:
        return {
            "success": False,
            "user": None,
            "error": "Cliente Supabase indisponível."
        }

    try:
        signup_options = {}
        if clean_name:
            signup_options["data"] = {"full_name": clean_name}

        res = client.auth.sign_up({
            "email": clean_email,
            "password": password,
            "options": signup_options
        })
        if res.user:
            return {
                "success": True,
                "user": {
                    "user_id": str(res.user.id),
                    "email": res.user.email or clean_email,
                    "display_name": clean_name or clean_email.split("@")[0].capitalize(),
                    "is_authenticated": True,
                    "is_guest": False,
                    "access_token": res.session.access_token if res.session else None
                },
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

def sign_out() -> bool:
    """Finaliza a sessão ativa no Supabase Auth."""
    if history_manager.is_supabase_configured():
        client = history_manager.get_supabase_client()
        if client:
            try:
                client.auth.sign_out()
            except Exception as e:
                print(f"Aviso ao realizar sign_out no Supabase: {e}")
    return True
