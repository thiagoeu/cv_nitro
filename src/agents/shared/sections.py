"""Estrutura do currículo em Markdown: rótulos por idioma, seções, marcadores e troca de seção."""
import re
from typing import Optional
from src.core import competency_matcher as competency_matcher_core

# Rótulos canônicos por idioma: o template do prompt usa estes valores para não vazar português em vagas EN/ES.
LABELS = {
    "pt": {
        "name": "PORTUGUÊS (Brasil)", "summary": "RESUMO PROFISSIONAL", "skills": "HABILIDADES TÉCNICAS",
        "experience": "EXPERIÊNCIA PROFISSIONAL", "projects": "PROJETOS EM DESTAQUE", "education": "FORMAÇÃO ACADÊMICA",
        "certifications": "CURSOS E CERTIFICAÇÕES", "languages": "IDIOMAS",
        "table_header": "| Categoria | Tecnologias & Conceitos |",
        "categories": "Back-end & Arquitetura, Front-end & Mobile, Banco de Dados & ORM, DevOps & Ferramentas",
        "repo": "Repositório",
    },
    "en": {
        "name": "INGLÊS (English)", "summary": "PROFESSIONAL SUMMARY", "skills": "TECHNICAL SKILLS",
        "experience": "WORK EXPERIENCE", "projects": "KEY PROJECTS", "education": "EDUCATION",
        "certifications": "CERTIFICATIONS", "languages": "LANGUAGES",
        "table_header": "| Category | Technologies & Concepts |",
        "categories": "Back-end & Architecture, Front-end & Mobile, Databases & ORM, DevOps & Tools",
        "repo": "Repository",
    },
    "es": {
        "name": "ESPANHOL (Español)", "summary": "RESUMEN PROFESIONAL", "skills": "HABILIDADES TÉCNICAS",
        "experience": "EXPERIENCIA PROFESIONAL", "projects": "PROYECTOS DESTACADOS", "education": "FORMACIÓN ACADÉMICA",
        "certifications": "CURSOS Y CERTIFICACIONES", "languages": "IDIOMAS",
        "table_header": "| Categoría | Tecnologías y Conceptos |",
        "categories": "Back-end y Arquitectura, Front-end y Mobile, Bases de Datos y ORM, DevOps y Herramientas",
        "repo": "Repositorio",
    },
}


PLACEHOLDER_RE = re.compile(r"<[A-Za-zÀ-ÿ0-9\s/—–_.,:-]+>")


EMAIL_IN_BRACKETS_RE = re.compile(r"^<[^@\s]+@[^@\s]+\.[^@\s]+>$")


def unfilled_placeholders(markdown: str):
    """Marcadores <...> não substituídos; e-mails no formato <usuario@dominio> não contam."""
    return [m for m in PLACEHOLDER_RE.finditer(markdown) if not EMAIL_IN_BRACKETS_RE.match(m.group())]


def split_sections(markdown: str) -> list:
    """[(título, corpo)] na ordem do documento; o trecho antes do primeiro '## ' (cabeçalho) tem título None."""
    parts = re.split(r"(?m)^##[ \t]+(.+?)[ \t]*$", markdown)
    return [(None, parts[0])] + list(zip(parts[1::2], parts[2::2]))


def section_of(markdown: str, found) -> Optional[str]:
    """Título da primeira seção em que found(corpo) é verdadeiro; None se aparece antes no cabeçalho ou em lugar nenhum."""
    return next((title for title, body in split_sections(markdown) if found(body)), None)


def _norm_title(title: str) -> str:
    return competency_matcher_core._clean_term(re.sub(r"^[#\s]+|[#:\s]+$", "", title or ""))


def resolve_section(markdown: str, name: Optional[str], labels: dict) -> Optional[str]:
    """Título real do currículo para a seção indicada pelo revisor; aceita o nome em qualquer idioma de LABELS."""
    headers = {_norm_title(title): title for title, _ in split_sections(markdown) if title}
    target = _norm_title(name)
    if target in headers:
        return headers[target]
    for lang_labels in LABELS.values():
        for key, label in lang_labels.items():
            if _norm_title(label) == target:
                return headers.get(_norm_title(labels[key]))
    return None


def splice_markdown_section(full_markdown: str, target_section_title: str, new_section_content: str) -> str:
    """
    Substitui cirurgicamente o bloco de uma seção Markdown específica pelo novo conteúdo fornecido.
    Localiza a seção pelo cabeçalho (## Título) de forma case-insensitive e tolerante a espaços.
    Garante integridade estrutural e fallback seguro caso a seção não seja encontrada.
    """
    if not full_markdown or not target_section_title:
        return full_markdown
    
    clean_title = re.sub(r"^[#\s]+|[#:\s]+$", "", target_section_title).strip()
    if not clean_title:
        return full_markdown

    # Normaliza new_section_content para conter o cabeçalho se omitido
    formatted_new = new_section_content.strip()
    if not re.match(r"^##\s+", formatted_new):
        formatted_new = f"## {clean_title}\n{formatted_new}"
    if not formatted_new.endswith("\n"):
        formatted_new += "\n\n"
    else:
        formatted_new += "\n"

    # Regex para encontrar a seção alvo: inicia no cabeçalho e vai até o próximo ## ou fim do texto
    pattern = rf"(?im)(^##\s*{re.escape(clean_title)}[^\n]*\n)(?:[\s\S]*?)(?=(?:^##\s+|\Z))"
    match = re.search(pattern, full_markdown)
    if match:
        return full_markdown[:match.start()] + formatted_new + full_markdown[match.end():].lstrip()

    # Fallback de busca aproximada por substring de cabeçalho
    approx_pattern = rf"(?im)(^##\s*[^\n]*{re.escape(clean_title)}[^\n]*\n)(?:[\s\S]*?)(?=(?:^##\s+|\Z))"
    approx_match = re.search(approx_pattern, full_markdown)
    if approx_match:
        return full_markdown[:approx_match.start()] + formatted_new + full_markdown[approx_match.end():].lstrip()

    return full_markdown
