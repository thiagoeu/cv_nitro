"""Leitura e serialização de candidaturas em arquivos Markdown locais com cabeçalho JSON."""
import os
import json
from typing import Dict, Any

COVER_LETTER_DELIMITER = "\n<!-- COVER_LETTER -->\n"


def _empty_application() -> Dict[str, Any]:
    return {"resume_md": "", "cover_letter_md": "", "metadata": {}}


def read_local_application(filepath: str) -> Dict[str, Any]:
    """Lê um arquivo do histórico local (cabeçalho JSON + currículo + carta), sem checar o dono."""
    if not filepath or not os.path.exists(filepath):
        return _empty_application()

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    body = content
    if content.startswith("<!--"):
        end_idx = content.find("-->")
        if end_idx != -1:
            try:
                metadata = json.loads(content[4:end_idx].strip())
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


def serialize_local_application(metadata: Dict[str, Any], content: str, cover_letter: str = "") -> str:
    """Serializa metadados JSON, currículo Markdown e carta de apresentação opcional no formato local."""
    file_content = f"<!--\n{json.dumps(metadata, ensure_ascii=False)}\n-->\n\n{content.strip()}"
    if cover_letter and cover_letter.strip():
        file_content += f"{COVER_LETTER_DELIMITER}{cover_letter.strip()}"
    return file_content

