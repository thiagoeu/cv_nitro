import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.core import history_manager

def get_profiles_dir() -> str:
    return os.environ.get("PROFILES_DIR", "profiles")

def _ensure_profiles_dir():
    d = get_profiles_dir()
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def get_default_profile(user_id: str, email: str = "") -> Dict[str, Any]:
    """Retorna um perfil vazio inicial com a estrutura padrão."""
    return {
        "user_id": user_id,
        "email": email,
        "full_name": "",
        "base_resume": "",
        "github_username": "",
        "cached_repos": [],
        "skills": [],
        "updated_at": datetime.now().astimezone().isoformat()
    }

def get_user_profile(user_id: str, email: str = "") -> Dict[str, Any]:
    """
    Recupera o perfil do usuário no Supabase ou no armazenamento local.
    Retorna o perfil completo com currículo base e cache de repositórios.
    """
    if not user_id:
        return get_default_profile("anonymous")

    # 1. Tenta recuperar do Supabase se configurado
    if history_manager.is_supabase_configured():
        client = history_manager.get_supabase_client()
        if client:
            try:
                res = client.table("user_profiles").select("*").eq("user_id", user_id).execute()
                if res.data and len(res.data) > 0:
                    row = res.data[0]
                    return {
                        "user_id": str(row.get("user_id")),
                        "email": row.get("email") or email,
                        "full_name": row.get("full_name") or "",
                        "base_resume": row.get("base_resume") or "",
                        "github_username": row.get("github_username") or "",
                        "cached_repos": row.get("cached_repos") or [],
                        "skills": row.get("skills") or [],
                        "updated_at": row.get("updated_at") or ""
                    }
            except Exception as e:
                print(f"Aviso ao consultar perfil no Supabase: {e}")

    # 2. Fallback no armazenamento local
    _ensure_profiles_dir()
    local_path = os.path.join(get_profiles_dir(), f"{user_id}.json")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "user_id": str(data.get("user_id", user_id)),
                    "email": data.get("email", email),
                    "full_name": data.get("full_name", ""),
                    "base_resume": data.get("base_resume", ""),
                    "github_username": data.get("github_username", ""),
                    "cached_repos": data.get("cached_repos", []),
                    "skills": data.get("skills", []),
                    "updated_at": data.get("updated_at", "")
                }
        except Exception as e:
            print(f"Aviso ao ler perfil local {local_path}: {e}")

    return get_default_profile(user_id, email)

def save_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """
    Persiste o perfil do usuário no Supabase (se ativo) e no armazenamento local.
    """
    if not user_id:
        return False

    now_iso = datetime.now().astimezone().isoformat()
    clean_data = {
        "user_id": user_id,
        "email": (profile_data.get("email") or "").strip(),
        "full_name": (profile_data.get("full_name") or "").strip(),
        "base_resume": (profile_data.get("base_resume") or "").strip(),
        "github_username": (profile_data.get("github_username") or "").strip(),
        "cached_repos": profile_data.get("cached_repos") or [],
        "skills": profile_data.get("skills") or [],
        "updated_at": now_iso
    }

    # 1. Salva no Supabase
    if history_manager.is_supabase_configured():
        client = history_manager.get_supabase_client()
        if client:
            try:
                # Usa upsert para criar ou atualizar em um único comando
                client.table("user_profiles").upsert(clean_data).execute()
            except Exception as e:
                print(f"Aviso ao salvar perfil no Supabase: {e}")

    # 2. Salva localmente (cache / fallback)
    _ensure_profiles_dir()
    local_path = os.path.join(get_profiles_dir(), f"{user_id}.json")
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar perfil local: {e}")
        return False

def update_cached_github_repos(user_id: str, repos: List[Dict[str, Any]]) -> bool:
    """
    Atualiza apenas o cache de repositórios do GitHub do perfil do candidato.
    """
    profile = get_user_profile(user_id)
    profile["cached_repos"] = repos
    return save_user_profile(user_id, profile)

def get_cached_github_repos(user_id: str) -> List[Dict[str, Any]]:
    """
    Retorna a lista de repositórios cacheados no perfil do candidato.
    """
    profile = get_user_profile(user_id)
    return profile.get("cached_repos") or []
