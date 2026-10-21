import os
import glob
from datetime import datetime
import json
import uuid
from typing import List, Dict, Any, Optional
from src.core import config

COVER_LETTER_DELIMITER = "\n<!-- COVER_LETTER -->\n"

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
    """Retorna uma instância conectada do cliente Supabase ou None em caso de falha/ausência."""
    if not is_supabase_configured():
        return None
    try:
        from supabase import create_client
        url = getattr(config, "SUPABASE_URL", None) or os.getenv("SUPABASE_URL")
        key = getattr(config, "SUPABASE_KEY", None) or os.getenv("SUPABASE_KEY")
        return create_client(url, key)
    except Exception as e:
        print(f"Aviso ao inicializar cliente Supabase: {e}")
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
    diagnostic: Optional[Dict[str, Any]] = None
) -> str:
    """
    Salva uma candidatura (currículo, carta, metadados e diagnóstico).
    Prioriza o Supabase quando configurado, mantendo gravação no histórico local como fallback.
    Retorna o identificador/caminho da candidatura salva.
    """
    _ensure_dir()
    now_iso = datetime.now().isoformat()
    techs = technologies or []
    diag = diagnostic or {}

    supabase_id = None
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
            if filepath and filepath.startswith("supabase:"):
                app_id = filepath.replace("supabase:", "")
                supabase_client.table("applications").update(payload).eq("id", app_id).execute()
                supabase_id = app_id
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

    return f"supabase:{supabase_id}" if (supabase_id and not filepath) else local_filepath

def list_resumes() -> List[Dict[str, Any]]:
    """
    Retorna a lista de candidaturas salvas, ordenadas pela mais recente.
    Consulta o Supabase primeiro; em caso de falha ou ausência, lê os arquivos locais.
    """
    supabase_client = get_supabase_client()
    if supabase_client:
        try:
            res = supabase_client.table("applications").select("*").order("created_at", desc=True).execute()
            if res.data:
                apps = []
                for row in res.data:
                    apps.append({
                        "job_title": row.get("job_title", "Vaga"),
                        "job_url": row.get("job_url", ""),
                        "language": row.get("language", "pt"),
                        "technologies": row.get("technologies") or [],
                        "date": row.get("created_at", datetime.now().isoformat()),
                        "has_cover_letter": row.get("has_cover_letter", bool(row.get("cover_letter_md"))),
                        "filepath": f"supabase:{row.get('id')}",
                        "filename": f"supabase_{row.get('id')}.md",
                        "diagnostic": row.get("diagnostic") or {}
                    })
                return apps
        except Exception as e:
            print(f"Erro ao listar do Supabase (utilizando fallback local): {e}")

    # Fallback local
    _ensure_dir()
    files = glob.glob(os.path.join(get_history_dir(), "*.md"))
    resumes = []

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

                metadata.setdefault("job_title", os.path.splitext(os.path.basename(file))[0])
                metadata.setdefault("job_url", "")
                metadata.setdefault("language", "pt")
                metadata.setdefault("technologies", [])
                metadata.setdefault("date", datetime.fromtimestamp(os.path.getmtime(file)).isoformat())
                metadata.setdefault("has_cover_letter", COVER_LETTER_DELIMITER.strip() in content)
                metadata.setdefault("diagnostic", {})

                metadata["filepath"] = file
                metadata["filename"] = os.path.basename(file)
                resumes.append(metadata)
        except Exception as e:
            print(f"Erro ao ler arquivo {file}: {e}")

    resumes.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return resumes

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
                            "diagnostic": row.get("diagnostic") or {}
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

def load_resume(filepath: str) -> str:
    """Mantém retrocompatibilidade retornando apenas o Markdown do currículo otimizado."""
    app_data = load_application(filepath)
    return app_data["resume_md"]

def load_cover_letter(filepath: str) -> str:
    """Retorna a carta de apresentação associada ao arquivo histórico (se houver)."""
    app_data = load_application(filepath)
    return app_data["cover_letter_md"]
