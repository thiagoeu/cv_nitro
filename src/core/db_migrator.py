import os
from typing import Dict, Any
from src.core import history_manager

def get_profiles_dir() -> str:
    return os.environ.get("PROFILES_DIR", "profiles")

def ensure_profiles_dir() -> str:
    p = get_profiles_dir()
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)
    return p

def check_or_setup_tables() -> Dict[str, Any]:
    """
    Verifica se a infraestrutura de tabelas (Supabase e local) está pronta para uso.
    Retorna o diagnóstico de prontidão das tabelas applications e user_profiles.
    """
    ensure_profiles_dir()
    
    result = {
        "supabase_connected": False,
        "applications_ready": False,
        "user_profiles_ready": False,
        "local_ready": True,
        "message": ""
    }

    if not history_manager.is_supabase_configured():
        result["message"] = "Supabase não configurado. Modo de armazenamento local ativo."
        return result

    client = history_manager.get_supabase_client()
    if not client:
        result["message"] = "Não foi possível instanciar o cliente Supabase."
        return result

    result["supabase_connected"] = True

    # 1. Verifica tabela applications
    try:
        res_apps = client.table("applications").select("id").limit(1).execute()
        result["applications_ready"] = True
    except Exception as e:
        result["message"] = f"Aviso ao consultar tabela applications: {e}"

    # 2. Verifica tabela user_profiles
    try:
        res_prof = client.table("user_profiles").select("user_id").limit(1).execute()
        result["user_profiles_ready"] = True
        result["message"] = "Todas as tabelas do Supabase (applications e user_profiles) estão prontas!"
    except Exception as e:
        result["user_profiles_ready"] = False
        result["message"] = (
            "A tabela 'user_profiles' ainda não foi criada no Supabase. "
            "Execute o script 'supabase_schema.sql' no SQL Editor do painel do Supabase."
        )

    return result

if __name__ == "__main__":
    status = check_or_setup_tables()
    print("Status do Banco:", status)
