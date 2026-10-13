import os
import glob
from datetime import datetime
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple

def get_history_dir() -> str:
    return os.environ.get("HISTORY_DIR", "history")

COVER_LETTER_DELIMITER = "\n<!-- COVER_LETTER -->\n"

def _ensure_dir():
    d = get_history_dir()
    if not os.path.exists(d):
        os.makedirs(d)

def save_resume(
    job_title: str,
    content: str,
    job_url: str = "",
    cover_letter: str = "",
    language: str = "pt",
    technologies: Optional[List[str]] = None
) -> str:
    """
    Salva um currículo gerado e opcionalmente sua Cover Letter como um arquivo markdown no histórico.
    Retorna o caminho do arquivo gerado.
    """
    _ensure_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c if c.isalnum() else "_" for c in job_title]).strip("_")
    filename = f"{timestamp}_{safe_title}_{uuid.uuid4().hex[:6]}.md"
    filepath = os.path.join(get_history_dir(), filename)
    
    metadata = {
        "job_title": job_title,
        "job_url": job_url.strip(),
        "language": language,
        "technologies": technologies or [],
        "date": datetime.now().isoformat(),
        "has_cover_letter": bool(cover_letter.strip())
    }
    
    file_content = f"<!--\n{json.dumps(metadata, ensure_ascii=False)}\n-->\n\n{content.strip()}"
    if cover_letter and cover_letter.strip():
        file_content += f"{COVER_LETTER_DELIMITER}{cover_letter.strip()}"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_content)
        
    return filepath

def list_resumes() -> List[Dict[str, Any]]:
    """
    Retorna uma lista de dicionários contendo metadados das candidaturas do histórico,
    ordenados pelo mais recente.
    """
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
                
                # Normaliza campos padrão
                metadata.setdefault("job_title", os.path.splitext(os.path.basename(file))[0])
                metadata.setdefault("job_url", "")
                metadata.setdefault("language", "pt")
                metadata.setdefault("technologies", [])
                metadata.setdefault("date", datetime.fromtimestamp(os.path.getmtime(file)).isoformat())
                metadata.setdefault("has_cover_letter", COVER_LETTER_DELIMITER.strip() in content)
                
                metadata["filepath"] = file
                metadata["filename"] = os.path.basename(file)
                resumes.append(metadata)
        except Exception as e:
            print(f"Erro ao ler arquivo {file}: {e}")
            
    # Ordenar por data decrescente
    resumes.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return resumes

def load_application(filepath: str) -> Dict[str, Any]:
    """
    Carrega a aplicação completa: metadados, texto do currículo e carta de apresentação.
    """
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
    """
    Mantém retrocompatibilidade retornando apenas o Markdown do currículo otimizado.
    """
    app_data = load_application(filepath)
    return app_data["resume_md"]

def load_cover_letter(filepath: str) -> str:
    """
    Retorna a carta de apresentação associada ao arquivo histórico (se houver).
    """
    app_data = load_application(filepath)
    return app_data["cover_letter_md"]
