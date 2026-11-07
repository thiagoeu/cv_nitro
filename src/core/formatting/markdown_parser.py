"""Parser e serializador estruturado para o editor de currículo com layout travado."""
from typing import Dict, Any, List


def parse_resume_markdown(markdown_content: str) -> Dict[str, Any]:
    """
    Analisa o Markdown do currículo no formato canônico ATS e extrai
    seus componentes estruturados para permitir edição segura de campos:
    - name: Nome do candidato (H1)
    - role: Cargo Alvo (H3 antes das seções)
    - contact: Linha de contato/links
    - sections: Lista de seções [{'title': '...', 'content': '...'}]
    """
    if not markdown_content:
        return {"name": "", "role": "", "contact": "", "sections": []}

    lines = markdown_content.splitlines()
    name = ""
    role = ""
    contact = ""
    sections: List[Dict[str, str]] = []

    current_sec_title = None
    current_sec_lines: List[str] = []
    in_header = True

    for raw_line in lines:
        line = raw_line.strip()

        # Detecção de nova seção principal H2
        if line.startswith("## "):
            in_header = False
            if current_sec_title is not None:
                sections.append({
                    "title": current_sec_title,
                    "content": "\n".join(current_sec_lines).strip()
                })
            current_sec_title = line[3:].strip()
            current_sec_lines = []
            continue

        if in_header:
            if line.startswith("# ") and not name:
                name = line[2:].strip()
                continue
            if line.startswith("### ") and not role:
                role = line[4:].strip()
                continue
            if ("|" in line or "@" in line) and not line.startswith("|") and not contact:
                contact = line
                continue
            if line and not contact and not name and not role:
                contact = line
                continue
        else:
            if current_sec_title is not None:
                current_sec_lines.append(raw_line)

    if current_sec_title is not None:
        sections.append({
            "title": current_sec_title,
            "content": "\n".join(current_sec_lines).strip()
        })

    return {
        "name": name,
        "role": role,
        "contact": contact,
        "sections": sections
    }


def serialize_resume_markdown(data: Dict[str, Any]) -> str:
    """
    Serializa os campos estruturados de volta para a especificação canônica
    Markdown de currículo ATS, mantendo o layout travado e padronizado.
    """
    lines: List[str] = []
    name = (data.get("name") or "").strip()
    role = (data.get("role") or "").strip()
    contact = (data.get("contact") or "").strip()
    sections = data.get("sections") or []

    if name:
        lines.append(f"# {name}")
    if role:
        lines.append(f"### {role}")
    if contact:
        lines.append(contact)

    if name or role or contact:
        lines.append("")

    for sec in sections:
        title = (sec.get("title") or "").strip()
        content = (sec.get("content") or "").strip()
        if title:
            lines.append(f"## {title}")
        if content:
            lines.append(content)
        lines.append("")

    return "\n".join(lines).strip()

