import os
import glob
from datetime import datetime
import json
import uuid
from typing import List, Dict, Any, Optional
from src.core import config

COVER_LETTER_DELIMITER = "\n<!-- COVER_LETTER -->\n"

# Singleton do cliente Supabase para reaproveitamento de conexão HTTP/TLS
_supabase_client_instance = None
_last_client_config = None

def get_history_dir() -> str:
    return os.environ.get("HISTORY_DIR", "history")

def _ensure_dir():
    d = get_history_dir()
    if not os.path.exists(d):
        os.makedirs(d)

def is_supabase_configured() -> bool:
    """Verifica se as variáveis de conexão com o Supabase estão presentes."""
    url = getattr(config, "SUPABASE_URL", None) or os.getenv("SUPABASE_URL")
    key = getattr(config, "SUPABASE_KEY", None) or os.getenv("SUPABASE_KEY")
    return bool(url and key and "your-project" not in url)

def get_supabase_client():
    """Retorna uma instância singleton conectada do cliente Supabase ou None em caso de falha/ausência."""
    global _supabase_client_instance, _last_client_config
    if not is_supabase_configured():
        _supabase_client_instance = None
        _last_client_config = None
        return None

    raw_url = getattr(config, "SUPABASE_URL", None) or os.getenv("SUPABASE_URL") or ""
    key = (getattr(config, "SUPABASE_KEY", None) or os.getenv("SUPABASE_KEY") or "").strip()
    current_config = (raw_url, key)

    if _supabase_client_instance is not None and _last_client_config == current_config:
        return _supabase_client_instance

    try:
        from supabase import create_client
        url = raw_url.strip().rstrip("/")
        if url.endswith("/rest/v1"):
            url = url[:-len("/rest/v1")].rstrip("/")
        _supabase_client_instance = create_client(url, key)
        _last_client_config = current_config
        return _supabase_client_instance
    except Exception as e:
        print(f"Aviso ao inicializar cliente Supabase: {e}")
        return None

def _parse_datetime_naive(date_val: Any) -> datetime:
    """Extrai objeto datetime sem tzinfo (horário civil de criação) para comparação consistente."""
    if not date_val:
        return datetime.min
    if isinstance(date_val, datetime):
        return date_val.replace(tzinfo=None)
    s = str(date_val).strip()
    if s.endswith("Z"):
        s = s[:-1]
    # Remove offset +00:00 ou -03:00 etc para pegar o horário civil gravado
    if "+" in s:
        s = s.split("+")[0]
    elif "-" in s[10:]:  # offset negativo depois de YYYY-MM-DD
        idx = s.rfind("-")
        if idx > 10:
            s = s[:idx]
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return datetime.min

def _get_sort_timestamp(date_val: Any) -> float:
    """Converte datas em qualquer formato para timestamp numérico civil."""
    dt = _parse_datetime_naive(date_val)
    if dt == datetime.min:
        return 0.0
    return dt.timestamp()

def format_display_date(date_val: Any) -> str:
    """Formata data para exibição amigável no formato DD/MM/YYYY HH:MM."""
    try:
        dt = _parse_datetime_naive(date_val)
        if dt != datetime.min:
            return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return str(date_val)[:16].replace("T", " ")

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
    diagnostic: Optional[Dict[str, Any]] = None
) -> str:
    """
    Salva ou atualiza uma candidatura (currículo, carta, metadados e diagnóstico).
    Prioriza o Supabase quando configurado, mantendo gravação no histórico local como fallback.
    Previne duplicatas checando e reaproveitando IDs existentes.
    """
    _ensure_dir()
    now_iso = datetime.now().isoformat()
    techs = technologies or []
    diag = diagnostic or {}

    supabase_id = None
    # 1. Checa se o filepath fornecido já identifica o registro no Supabase
    if filepath and filepath.startswith("supabase:"):
        supabase_id = filepath.replace("supabase:", "")
    elif filepath and os.path.exists(filepath):
        # 2. Se for um arquivo local já existente, recupera o supabase_id gravado nele para atualizar e não duplicar
        try:
            existing_data = load_application(filepath)
            existing_sub_id = existing_data.get("metadata", {}).get("supabase_id")
            if existing_sub_id:
                supabase_id = existing_sub_id
        except Exception:
            pass

    supabase_client = get_supabase_client()
    if supabase_client:
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
                # Atualização idempotente (evita duplicações no banco)
                supabase_client.table("applications").update(payload).eq("id", supabase_id).execute()
            else:
                payload["created_at"] = now_iso
                res = supabase_client.table("applications").insert(payload).execute()
                if res.data and len(res.data) > 0:
                    supabase_id = res.data[0].get("id")
        except Exception as e:
            print(f"Erro ao salvar no Supabase (utilizando fallback local): {e}")

    # Gravação local (cache/fallback)
    if not filepath or filepath.startswith("supabase:"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join([c if c.isalnum() else "_" for c in job_title]).strip("_")
        filename = f"{timestamp}_{safe_title}_{uuid.uuid4().hex[:6]}.md"
        local_filepath = os.path.join(get_history_dir(), filename)
    else:
        local_filepath = filepath

    metadata = {
        "job_title": job_title,
        "job_url": (job_url or "").strip(),
        "language": language,
        "technologies": techs,
        "date": now_iso,
        "has_cover_letter": bool((cover_letter or "").strip()),
        "job_description": (job_description or "").strip(),
        "base_resume": (base_resume or "").strip(),
        "github_username": (github_username or "").strip(),
        "diagnostic": diag
    }
    if supabase_id:
        metadata["supabase_id"] = supabase_id

    file_content = f"<!--\n{json.dumps(metadata, ensure_ascii=False)}\n-->\n\n{content.strip()}"
    if cover_letter and cover_letter.strip():
        file_content += f"{COVER_LETTER_DELIMITER}{cover_letter.strip()}"

    with open(local_filepath, "w", encoding="utf-8") as f:
        f.write(file_content)

    if filepath and filepath.startswith("supabase:"):
        return filepath
    if supabase_id:
        return f"supabase:{supabase_id}"
    return local_filepath

def list_resumes() -> List[Dict[str, Any]]:
    """
    Retorna a lista unificada de candidaturas salvas, ordenadas estritamente
    da mais recente para a mais antiga (ordem cronológica decrescente).
    Mescla registros do Supabase com o histórico local sem duplicá-los.
    """
    resumes_map: Dict[str, Dict[str, Any]] = {}
    known_supabase_ids = set()

    # 1. Consulta o Supabase se configurado
    supabase_client = get_supabase_client()
    if supabase_client:
        try:
            res = supabase_client.table("applications").select("*").order("created_at", desc=True).execute()
            if res.data:
                for row in res.data:
                    row_id = str(row.get("id"))
                    known_supabase_ids.add(row_id)
                    item = {
                        "job_title": row.get("job_title", "Vaga"),
                        "job_url": row.get("job_url", ""),
                        "language": row.get("language", "pt"),
                        "technologies": row.get("technologies") or [],
                        "date": row.get("created_at", datetime.now().isoformat()),
                        "has_cover_letter": row.get("has_cover_letter", bool(row.get("cover_letter_md"))),
                        "filepath": f"supabase:{row_id}",
                        "filename": f"supabase_{row_id}.md",
                        "diagnostic": row.get("diagnostic") or {},
                        "supabase_id": row_id
                    }
                    resumes_map[f"supabase:{row_id}"] = item
        except Exception as e:
            print(f"Erro ao listar do Supabase (utilizando fallback local): {e}")

    # 2. Varre os arquivos locais em history/
    _ensure_dir()
    files = glob.glob(os.path.join(get_history_dir(), "*.md"))

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                metadata = {}
                if content.startswith("<!--"):
                    end_idx = content.find("-->")
                    if end_idx != -1:
                        meta_str = content[4:end_idx].strip()
                        metadata = json.loads(meta_str)

                sub_id = metadata.get("supabase_id")
                # Se este arquivo local já está registrado e listado pelo Supabase, não duplica
                if sub_id and str(sub_id) in known_supabase_ids:
                    continue

                metadata.setdefault("job_title", os.path.splitext(os.path.basename(file))[0])
                metadata.setdefault("job_url", "")
                metadata.setdefault("language", "pt")
                metadata.setdefault("technologies", [])
                metadata.setdefault("date", datetime.fromtimestamp(os.path.getmtime(file)).isoformat())
                metadata.setdefault("has_cover_letter", COVER_LETTER_DELIMITER.strip() in content)
                metadata.setdefault("diagnostic", {})

                metadata["filepath"] = file
                metadata["filename"] = os.path.basename(file)
                
                # Chave única para o mapa local
                key = f"local:{file}"
                resumes_map[key] = metadata
        except Exception as e:
            print(f"Erro ao ler arquivo {file}: {e}")

    all_resumes = list(resumes_map.values())

    # 3. Ordenação rigorosa da mais recente para a mais antiga
    all_resumes.sort(key=lambda x: _get_sort_timestamp(x.get("date")), reverse=True)
    return all_resumes

def load_application(filepath: str) -> Dict[str, Any]:
    """
    Carrega os dados completos da candidatura (currículo, carta e metadados).
    Suporta tanto IDs do Supabase (supabase:<id>) quanto caminhos locais de arquivo.
    """
    if filepath.startswith("supabase:"):
        app_id = filepath.replace("supabase:", "")
        supabase_client = get_supabase_client()
        if supabase_client:
            try:
                res = supabase_client.table("applications").select("*").eq("id", app_id).single().execute()
                if res.data:
                    row = res.data
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
                            "supabase_id": app_id
                        }
                    }
            except Exception as e:
                print(f"Erro ao carregar candidatura do Supabase ({filepath}): {e}")

    # Leitura local
    if not os.path.exists(filepath):
        return {"resume_md": "", "cover_letter_md": "", "metadata": {}}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    body = content
    if content.startswith("<!--"):
        end_idx = content.find("-->")
        if end_idx != -1:
            try:
                meta_str = content[4:end_idx].strip()
                metadata = json.loads(meta_str)
            except Exception:
                pass
            body = content[end_idx + 3:].strip()

    metadata.setdefault("diagnostic", {})
    resume_part = body
    cover_letter_part = ""
    if COVER_LETTER_DELIMITER.strip() in body:
        parts = body.split(COVER_LETTER_DELIMITER.strip())
        resume_part = parts[0].strip()
        cover_letter_part = parts[1].strip() if len(parts) > 1 else ""

    return {
        "resume_md": resume_part,
        "cover_letter_md": cover_letter_part,
        "metadata": metadata
    }

def delete_application(filepath: str) -> bool:
    """
    Exclui uma candidatura do Supabase e/ou do armazenamento local.
    """
    deleted = False
    supabase_client = get_supabase_client()

    # 1. Se for identificador do Supabase
    if filepath.startswith("supabase:"):
        app_id = filepath.replace("supabase:", "")
        if supabase_client:
            try:
                supabase_client.table("applications").delete().eq("id", app_id).execute()
                deleted = True
            except Exception as e:
                print(f"Erro ao excluir do Supabase: {e}")

        # Procura se há arquivo local com esse supabase_id
        files = glob.glob(os.path.join(get_history_dir(), "*.md"))
        for f in files:
            try:
                data = load_application(f)
                if data.get("metadata", {}).get("supabase_id") == app_id:
                    os.remove(f)
                    deleted = True
            except Exception:
                pass

    # 2. Se for arquivo local
    elif os.path.exists(filepath):
        try:
            data = load_application(filepath)
            sub_id = data.get("metadata", {}).get("supabase_id")
            if sub_id and supabase_client:
                try:
                    supabase_client.table("applications").delete().eq("id", sub_id).execute()
                except Exception as e:
                    print(f"Erro ao excluir registro associado do Supabase: {e}")
            os.remove(filepath)
            deleted = True
        except Exception as e:
            print(f"Erro ao remover arquivo local {filepath}: {e}")

    return deleted

def clean_test_records_from_supabase() -> int:
    """Remove registros de testes automatizados conhecidos do Supabase."""
    client = get_supabase_client()
    if not client:
        return 0
    test_titles = [
        "Staff AI Agent Engineer",
        "Senior Python Engineer",
        "Full Stack Engineer",
        "Cloud Architect"
    ]
    deleted_count = 0
    try:
        for title in test_titles:
            res = client.table("applications").delete().eq("job_title", title).execute()
            if res.data:
                deleted_count += len(res.data)
    except Exception as e:
        print(f"Erro ao limpar registros de teste: {e}")
    return deleted_count

def sync_local_to_supabase() -> int:
    """Sincroniza currículos locais que ainda não possuem registro no Supabase."""
    client = get_supabase_client()
    if not client:
        return 0
    synced = 0
    files = glob.glob(os.path.join(get_history_dir(), "*.md"))
    for file in files:
        try:
            app_data = load_application(file)
            meta = app_data.get("metadata", {})
            if meta.get("supabase_id"):
                continue
            job_title = meta.get("job_title", "")
            if not job_title:
                continue

            payload = {
                "job_title": job_title,
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
                "created_at": meta.get("date") or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            res = client.table("applications").insert(payload).execute()
            if res.data and len(res.data) > 0:
                sub_id = res.data[0].get("id")
                meta["supabase_id"] = sub_id
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

def load_resume(filepath: str) -> str:
    """Mantém retrocompatibilidade retornando apenas o Markdown do currículo otimizado."""
    app_data = load_application(filepath)
    return app_data["resume_md"]

def load_cover_letter(filepath: str) -> str:
    """Retorna a carta de apresentação associada ao arquivo histórico (se houver)."""
    app_data = load_application(filepath)
    return app_data["cover_letter_md"]
