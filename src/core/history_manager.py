import os
import glob
from datetime import datetime
import json
import uuid
from typing import List, Dict, Any, Optional
from src.core import config
from src.core.storage.date_utils import (
    _parse_datetime_naive,
    _get_sort_timestamp,
    format_display_date,
)
from src.core.storage.local_store import (
    COVER_LETTER_DELIMITER,
    _empty_application,
    read_local_application as _read_local,
    serialize_local_application,
)

GUEST_USER_ID = "guest_local"
SUPABASE_SETTINGS = ("SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_ROLE_KEY")
# Colunas da listagem: currículo, vaga e currículo base só são lidos ao abrir a candidatura
LIST_COLUMNS = "id,user_id,job_title,job_url,language,technologies,created_at,has_cover_letter,diagnostic"

# Singleton do cliente de dados (service role): nunca autentica usuários, então pode ser compartilhado
_supabase_client_instance = None
_last_client_config = None


def get_history_dir() -> str:
    return os.environ.get("HISTORY_DIR", "history")


def _ensure_dir():
    d = get_history_dir()
    if not os.path.exists(d):
        os.makedirs(d)


def missing_supabase_settings() -> List[str]:
    """Variáveis do Supabase ausentes ou com valor de exemplo; faltando qualquer uma, o app roda em modo local."""
    return [name for name in SUPABASE_SETTINGS if not getattr(config, name, None) or "your-" in getattr(config, name)]


def is_supabase_configured() -> bool:
    """Modo nuvem exige URL, chave anon (login) e chave service role (dados)."""
    return not missing_supabase_settings()


def supabase_url() -> str:
    url = (config.SUPABASE_URL or "").strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-len("/rest/v1")].rstrip("/")
    return url


def get_supabase_client():
    """Cliente de dados (service role) singleton, ou None sem configuração/falha."""
    global _supabase_client_instance, _last_client_config
    if not is_supabase_configured():
        _supabase_client_instance = None
        _last_client_config = None
        return None

    current_config = (config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    if _supabase_client_instance is not None and _last_client_config == current_config:
        return _supabase_client_instance

    try:
        from supabase import create_client, ClientOptions
        _supabase_client_instance = create_client(
            supabase_url(),
            config.SUPABASE_SERVICE_ROLE_KEY.strip(),
            ClientOptions(auto_refresh_token=False, persist_session=False)
        )
        _last_client_config = current_config
        return _supabase_client_instance
    except Exception as e:
        print(f"Aviso ao inicializar cliente Supabase: {e}")
        return None


def owned(query, user_id: Optional[str]):
    """Único ponto de isolamento: a service role ignora o RLS, então toda query filtra o dono aqui."""
    if not user_id or user_id == GUEST_USER_ID:
        raise ValueError("Operação no banco exige um usuário autenticado.")
    return query.eq("user_id", user_id)


def _local_files() -> List[str]:
    _ensure_dir()
    return glob.glob(os.path.join(get_history_dir(), "*.md"))


def _local_copy_of(supabase_id: str) -> Optional[str]:
    """Caminho da cópia local de uma candidatura da nuvem, se existir."""
    for file in _local_files():
        try:
            if _read_local(file)["metadata"].get("supabase_id") == supabase_id:
                return file
        except Exception:
            pass
    return None


def save_resume(
    job_title: str,
    content: str,
    job_url: str = "",
    cover_letter: str = "",
    language: str = "pt",
    technologies: Optional[List[str]] = None,
    job_description: str = "",
    base_resume: str = "",
    github_username: str = "",
    filepath: Optional[str] = None,
    diagnostic: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Salva ou atualiza uma candidatura (currículo, carta, metadados e diagnóstico) do user_id.
    Grava no Supabase quando configurado e sempre mantém uma cópia local.
    Retorna 'supabase:<id>' se a nuvem gravou; caso contrário, o caminho local
    (com Supabase configurado, isso indica que a sincronização falhou).
    """
    _ensure_dir()
    now_iso = datetime.now().astimezone().isoformat()
    techs = technologies or []
    diag = diagnostic or {}

    # Identidade da candidatura existente: id na nuvem e cópia local
    supabase_id = None
    local_filepath = None
    if filepath and filepath.startswith("supabase:"):
        supabase_id = filepath[len("supabase:"):]
        local_filepath = _local_copy_of(supabase_id)
    elif filepath and os.path.exists(filepath):
        local_filepath = filepath
        supabase_id = _read_local(filepath)["metadata"].get("supabase_id")

    created_at = (_read_local(local_filepath)["metadata"].get("date") if local_filepath else None) or now_iso

    cloud_ok = False
    supabase_client = get_supabase_client()
    if supabase_client and user_id and user_id != GUEST_USER_ID:
        try:
            payload = {
                "job_title": job_title,
                "job_url": (job_url or "").strip(),
                "language": language,
                "technologies": techs,
                "resume_md": content.strip(),
                "cover_letter_md": (cover_letter or "").strip(),
                "has_cover_letter": bool((cover_letter or "").strip()),
                "job_description": (job_description or "").strip(),
                "base_resume": (base_resume or "").strip(),
                "github_username": (github_username or "").strip(),
                "diagnostic": diag,
                "updated_at": now_iso
            }
            if supabase_id:
                res = owned(supabase_client.table("applications").update(payload), user_id).eq("id", supabase_id).execute()
                cloud_ok = bool(res.data)
            else:
                payload["user_id"] = user_id
                payload["created_at"] = now_iso
                res = supabase_client.table("applications").insert(payload).execute()
                if res.data:
                    supabase_id = res.data[0].get("id")
                    cloud_ok = True
        except Exception as e:
            print(f"Erro ao salvar no Supabase (utilizando fallback local): {e}")

    if not local_filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join([c if c.isalnum() else "_" for c in job_title]).strip("_")
        local_filepath = os.path.join(get_history_dir(), f"{timestamp}_{safe_title}_{uuid.uuid4().hex[:6]}.md")

    metadata = {
        "job_title": job_title,
        "job_url": (job_url or "").strip(),
        "language": language,
        "technologies": techs,
        "date": created_at,
        "has_cover_letter": bool((cover_letter or "").strip()),
        "job_description": (job_description or "").strip(),
        "base_resume": (base_resume or "").strip(),
        "github_username": (github_username or "").strip(),
        "diagnostic": diag
    }
    if user_id:
        metadata["user_id"] = user_id
    if supabase_id:
        metadata["supabase_id"] = supabase_id

    file_content = serialize_local_application(metadata, content, cover_letter)

    with open(local_filepath, "w", encoding="utf-8") as f:
        f.write(file_content)

    return f"supabase:{supabase_id}" if cloud_ok else local_filepath


def _row_to_item(row: Dict[str, Any]) -> Dict[str, Any]:
    row_id = str(row.get("id"))
    return {
        "job_title": row.get("job_title", "Vaga"),
        "job_url": row.get("job_url", ""),
        "language": row.get("language", "pt"),
        "technologies": row.get("technologies") or [],
        "date": row.get("created_at") or "",
        "has_cover_letter": bool(row.get("has_cover_letter")),
        "filepath": f"supabase:{row_id}",
        "filename": f"supabase_{row_id}.md",
        "diagnostic": row.get("diagnostic") or {},
        "supabase_id": row_id,
        "user_id": str(row.get("user_id")) if row.get("user_id") else None
    }


def list_resumes(user_id: str) -> List[Dict[str, Any]]:
    """
    Candidaturas do user_id (nuvem + cópias locais sem duplicar), da mais recente para a mais antiga.
    Arquivos locais sem dono ou de outro usuário não aparecem.
    """
    resumes: List[Dict[str, Any]] = []
    known_supabase_ids = set()

    supabase_client = get_supabase_client()
    if supabase_client and user_id and user_id != GUEST_USER_ID:
        try:
            res = owned(supabase_client.table("applications").select(LIST_COLUMNS), user_id).order("created_at", desc=True).execute()
            for row in res.data or []:
                item = _row_to_item(row)
                known_supabase_ids.add(item["supabase_id"])
                resumes.append(item)
        except Exception as e:
            print(f"Erro ao listar do Supabase (utilizando fallback local): {e}")

    for file in _local_files():
        try:
            metadata = _read_local(file)["metadata"]
            if metadata.get("user_id") != user_id:
                continue
            # Já listado pela nuvem: não duplica
            if str(metadata.get("supabase_id")) in known_supabase_ids:
                continue

            metadata.setdefault("job_title", os.path.splitext(os.path.basename(file))[0])
            metadata.setdefault("job_url", "")
            metadata.setdefault("language", "pt")
            metadata.setdefault("technologies", [])
            metadata.setdefault("date", datetime.fromtimestamp(os.path.getmtime(file)).isoformat())
            metadata.setdefault("has_cover_letter", False)
            metadata["filepath"] = file
            metadata["filename"] = os.path.basename(file)
            resumes.append(metadata)
        except Exception as e:
            print(f"Erro ao ler arquivo {file}: {e}")

    resumes.sort(key=lambda x: _get_sort_timestamp(x.get("date")), reverse=True)
    return resumes


def load_application(filepath: str, user_id: str) -> Dict[str, Any]:
    """
    Carrega a candidatura completa (currículo, carta e metadados) do user_id.
    Suporta IDs do Supabase (supabase:<id>) e caminhos locais; candidatura de outro dono volta vazia.
    """
    if filepath.startswith("supabase:"):
        app_id = filepath[len("supabase:"):]
        supabase_client = get_supabase_client()
        if supabase_client:
            try:
                res = owned(supabase_client.table("applications").select("*"), user_id).eq("id", app_id).limit(1).execute()
                if res.data:
                    row = res.data[0]
                    return {
                        "resume_md": row.get("resume_md", ""),
                        "cover_letter_md": row.get("cover_letter_md", ""),
                        "metadata": {
                            "job_title": row.get("job_title", ""),
                            "job_url": row.get("job_url", ""),
                            "language": row.get("language", "pt"),
                            "technologies": row.get("technologies") or [],
                            "date": row.get("created_at", ""),
                            "has_cover_letter": row.get("has_cover_letter", False),
                            "job_description": row.get("job_description", ""),
                            "base_resume": row.get("base_resume", ""),
                            "github_username": row.get("github_username", ""),
                            "diagnostic": row.get("diagnostic") or {},
                            "supabase_id": app_id,
                            "user_id": user_id
                        }
                    }
            except Exception as e:
                print(f"Erro ao carregar candidatura do Supabase ({filepath}): {e}")
        return _empty_application()

    data = _read_local(filepath)
    if data["metadata"].get("user_id") != user_id:
        return _empty_application()
    return data


def delete_application(filepath: str, user_id: str) -> bool:
    """Exclui uma candidatura do user_id na nuvem e suas cópias locais."""
    deleted = False
    supabase_client = get_supabase_client()

    if filepath.startswith("supabase:"):
        sub_id = filepath[len("supabase:"):]
        local_paths = [f for f in _local_files() if _read_local(f)["metadata"].get("supabase_id") == sub_id]
    else:
        if not os.path.exists(filepath):
            return False
        sub_id = _read_local(filepath)["metadata"].get("supabase_id")
        local_paths = [filepath]

    if sub_id and supabase_client:
        try:
            res = owned(supabase_client.table("applications").delete(), user_id).eq("id", sub_id).execute()
            deleted = bool(res.data)
        except Exception as e:
            print(f"Erro ao excluir do Supabase: {e}")

    for path in local_paths:
        try:
            if _read_local(path)["metadata"].get("user_id") == user_id:
                os.remove(path)
                deleted = True
        except Exception as e:
            print(f"Erro ao remover arquivo local {path}: {e}")

    return deleted


def sync_local_to_supabase(user_id: str) -> int:
    """Envia à nuvem as candidaturas locais do user_id que ainda não têm registro no Supabase."""
    client = get_supabase_client()
    if not client or not user_id or user_id == GUEST_USER_ID:
        return 0
    synced = 0
    for file in _local_files():
        try:
            app_data = _read_local(file)
            meta = app_data["metadata"]
            if meta.get("user_id") != user_id or meta.get("supabase_id") or not meta.get("job_title"):
                continue

            payload = {
                "user_id": user_id,
                "job_title": meta["job_title"],
                "job_url": (meta.get("job_url") or "").strip(),
                "language": meta.get("language", "pt"),
                "technologies": meta.get("technologies") or [],
                "resume_md": (app_data.get("resume_md") or "").strip(),
                "cover_letter_md": (app_data.get("cover_letter_md") or "").strip(),
                "has_cover_letter": bool(app_data.get("cover_letter_md")),
                "job_description": (meta.get("job_description") or "").strip(),
                "base_resume": (meta.get("base_resume") or "").strip(),
                "github_username": (meta.get("github_username") or "").strip(),
                "diagnostic": meta.get("diagnostic") or {},
                "created_at": meta.get("date") or datetime.now().astimezone().isoformat(),
                "updated_at": datetime.now().astimezone().isoformat()
            }
            res = client.table("applications").insert(payload).execute()
            if res.data:
                meta["supabase_id"] = res.data[0].get("id")
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                parts = content.split("-->\n\n", 1)
                body = parts[1] if len(parts) > 1 else content
                with open(file, "w", encoding="utf-8") as f:
                    f.write(f"<!--\n{json.dumps(meta, ensure_ascii=False)}\n-->\n\n{body}")
                synced += 1
        except Exception as e:
            print(f"Erro ao sincronizar arquivo {file}: {e}")
    return synced
