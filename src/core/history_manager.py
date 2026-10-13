import os
import glob
from datetime import datetime
import json
import uuid

HISTORY_DIR = "history"

def _ensure_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def save_resume(job_title: str, content: str) -> str:
    """
    Salva um currículo gerado como um arquivo markdown no histórico.
    Retorna o caminho do arquivo gerado.
    """
    _ensure_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c if c.isalnum() else "_" for c in job_title]).strip("_")
    filename = f"{timestamp}_{safe_title}_{uuid.uuid4().hex[:6]}.md"
    filepath = os.path.join(HISTORY_DIR, filename)
    
    # Adicionando um frontmatter invisível para metadados simples
    metadata = {
        "job_title": job_title,
        "date": datetime.now().isoformat(),
    }
    
    file_content = f"<!--\n{json.dumps(metadata)}\n-->\n\n{content}"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(file_content)
        
    return filepath

def list_resumes() -> list:
    """
    Retorna uma lista de dicionários contendo metadados e o arquivo do histórico.
    Ordenados pelo mais recente.
    """
    _ensure_dir()
    files = glob.glob(os.path.join(HISTORY_DIR, "*.md"))
    resumes = []
    
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                # Extraindo frontmatter do comentário HTML
                if content.startswith("<!--"):
                    end_idx = content.find("-->")
                    if end_idx != -1:
                        meta_str = content[4:end_idx].strip()
                        metadata = json.loads(meta_str)
                        metadata["filepath"] = file
                        metadata["filename"] = os.path.basename(file)
                        resumes.append(metadata)
        except Exception as e:
            print(f"Erro ao ler arquivo {file}: {e}")
            
    # Ordenar por data decrescente
    resumes.sort(key=lambda x: x.get("date", ""), reverse=True)
    return resumes

def load_resume(filepath: str) -> str:
    """
    Carrega o conteúdo do currículo (sem os metadados HTML) a partir do caminho do arquivo.
    """
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if content.startswith("<!--"):
        end_idx = content.find("-->")
        if end_idx != -1:
            return content[end_idx + 3:].strip()
            
    return content.strip()
