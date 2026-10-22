import re
import html
from typing import Optional, List, Dict, Any

def format_resume_to_html(markdown_content: str, title: Optional[str] = None) -> str:
    """
    Converte o currículo em Markdown no layout canônico para um documento HTML estilizado,
    com visual profissional em folha A4 e regras de impressão (@media print) para PDF.
    """
    if not markdown_content:
        return "<html><body><p>Nenhum conteúdo para exibir.</p></body></html>"

    lines = markdown_content.strip().split("\n")
    html_body = []
    
    table_rows = []
    header_rows = 0  # linhas acima do separador "| --- |" são cabeçalho, em qualquer idioma

    def flush_table():
        nonlocal header_rows
        if not table_rows:
            return
        html_body.append("<div class='skills-table-container'><table class='skills-table'>")
        for r_idx, row in enumerate(table_rows):
            tag = "th" if r_idx < header_rows else "td"
            cells = "".join(
                f"<{tag} class='{'col-cat' if c_idx == 0 else 'col-tech'}'>{_inline_format(cell)}</{tag}>"
                for c_idx, cell in enumerate(row)
            )
            html_body.append(f"<tr>{cells}</tr>")
        html_body.append("</table></div>")
        table_rows.clear()
        header_rows = 0

    # Extrai o título se não foi passado
    doc_title = title or "Currículo Profissional"

    for raw_line in lines:
        line = raw_line.strip()

        # Linhas de tabela
        if line.startswith("|") and line.endswith("|"):
            # Linha divisória (| :--- | :--- |): tudo acima dela é cabeçalho
            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", line):
                header_rows = len(table_rows)
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                table_rows.append(cells)
            continue
        flush_table()

        if not line:
            continue

        # Header H1: Nome do Candidato
        if line.startswith("# "):
            name = line[2:].strip()
            doc_title = name
            html_body.append(f"<h1 class='candidate-name'>{html.escape(name)}</h1>")
            continue

        # Subtítulo H3: Cargo Alvo
        if line.startswith("### ") and not in_experience_or_projects(html_body):
            role = line[4:].strip()
            html_body.append(f"<div class='candidate-role'>{html.escape(role)}</div>")
            continue

        # Linha de contatos (Cidade | Email | etc.): só no cabeçalho, antes da primeira seção
        if "|" in line and not line.startswith("|") and not in_experience_or_projects(html_body):
            contacts = [c.strip() for c in line.split("|")]
            formatted_contacts = []
            for c in contacts:
                # Transforma links em <a>
                c_formatted = _format_contact_item(c)
                formatted_contacts.append(c_formatted)
            html_body.append(f"<div class='contact-bar'>{' &bull; '.join(formatted_contacts)}</div>")
            continue

        # Seções principais H2
        if line.startswith("## "):
            sec_name = line[3:].strip()
            html_body.append(f"<h2 class='section-title'>{html.escape(sec_name)}</h2>")
            continue

        # Subseções H3 dentro de experiência/projetos
        if line.startswith("### "):
            sub_title = line[4:].strip()
            html_body.append(f"<h3 class='entry-title'>{_inline_format(sub_title)}</h3>")
            continue

        # Subtítulo em itálico (*Cargo | Período | Local*), sem confundir com "* item" ou "**negrito**"
        if re.fullmatch(r"([*_])(?![*_\s]).+\1", line):
            meta_info = line.strip("*_").strip()
            html_body.append(f"<div class='entry-meta'>{html.escape(meta_info)}</div>")
            continue

        # Bullet points de impacto (- **Tópico:** ou - ● **Tópico:** ou • **Tópico:**)
        if line.startswith("-") or line.startswith("*") or line.startswith("●") or line.startswith("•"):
            # Remove só o marcador de lista e o ●/• opcional, preservando o "**" do negrito
            content = re.sub(r"^(?:[-*+]\s+)?[●•]?\s*", "", line)
            formatted_content = _inline_format(content)
            html_body.append(f"<div class='bullet-item'><span class='bullet-point'>●</span> <div class='bullet-text'>{formatted_content}</div></div>")
            continue

        # Parágrafos normais (ex: Resumo Profissional)
        html_body.append(f"<p class='paragraph'>{_inline_format(line)}</p>")

    flush_table()

    def _row_class(item: str) -> str:
        if any(cls in item for cls in ["candidate-name", "candidate-role", "contact-bar", "section-title", "entry-title", "entry-meta"]):
            return "print-page-row no-break-after"
        return "print-page-row"

    # Cada bloco vira uma linha da tabela de paginação: o navegador quebra a página
    # entre linhas e repete o <thead> (espaçador de topo) em TODAS as páginas.
    body_content = "\n".join(
        f"            <tr class='{_row_class(item)}'><td class='print-page-body'>{item}</td></tr>" for item in html_body
    )

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(doc_title)}</title>
    <style>
        :root {{
            --primary: #1e3a8a;
            --text-main: #1f2937;
            --text-muted: #4b5563;
            --border-color: #cbd5e1;
            --bg-page: #ffffff;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f1f5f9;
            color: var(--text-main);
            line-height: 1.5;
            font-size: 13.5px;
            padding: 20px;
        }}
        .no-print-bar {{
            max-width: 850px;
            margin: 0 auto 16px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            background: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        }}
        .no-print-info {{
            font-size: 13px;
            color: #475569;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .print-btn {{
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            border: none;
            padding: 9px 18px;
            font-size: 13.5px;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .print-btn:hover {{
            background: linear-gradient(135deg, #059669, #047857);
            box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
            transform: translateY(-1px);
        }}
        .resume-sheet {{
            background-color: var(--bg-page);
            max-width: 850px;
            margin: 0 auto;
            padding: 40px 50px;
            border-radius: 4px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        .candidate-name {{
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
            text-align: center;
            margin-bottom: 2px;
            letter-spacing: -0.5px;
        }}
        .candidate-role {{
            font-size: 15px;
            font-weight: 600;
            color: #2563eb;
            text-align: center;
            margin-bottom: 8px;
        }}
        .contact-bar {{
            font-size: 12.5px;
            color: var(--text-muted);
            text-align: center;
            margin-bottom: 24px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 12px;
        }}
        .contact-bar a {{
            color: var(--text-muted);
            text-decoration: none;
        }}
        .contact-bar a:hover {{
            color: #2563eb;
            text-decoration: underline;
        }}
        .section-title {{
            font-size: 14.5px;
            font-weight: 800;
            color: #0f172a;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-top: 22px;
            margin-bottom: 10px;
            border-bottom: 1.5px solid #0f172a;
            padding-bottom: 3px;
        }}
        .paragraph {{
            text-align: justify;
            margin-bottom: 12px;
            color: #334155;
            font-size: 13px;
        }}
        /* Tabela de Habilidades */
        .skills-table-container {{
            margin-bottom: 16px;
            overflow-x: auto;
        }}
        .skills-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
        }}
        .skills-table th, .skills-table td {{
            padding: 6px 10px;
            border: 1px solid #94a3b8;
            vertical-align: top;
        }}
        .skills-table .col-cat {{
            width: 28%;
            background-color: #f8fafc;
            font-weight: 700;
            color: #0f172a;
        }}
        .skills-table .col-tech {{
            color: #334155;
            line-height: 1.45;
        }}
        /* Experiência & Projetos */
        .entry-title {{
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
            margin-top: 14px;
            margin-bottom: 1px;
        }}
        .entry-meta {{
            font-size: 12.5px;
            font-style: italic;
            color: #475569;
            margin-bottom: 6px;
        }}
        .bullet-item {{
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 5px;
            font-size: 12.8px;
            color: #1e293b;
            text-align: justify;
            page-break-inside: avoid;
        }}
        .bullet-point {{
            font-size: 9px;
            color: #0f172a;
            flex-shrink: 0;
            position: relative;
            top: -1px;
        }}
        .bullet-text strong {{
            color: #0f172a;
            font-weight: 700;
        }}
        .bullet-text a {{
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
        }}
        .bullet-text a:hover {{
            text-decoration: underline;
        }}
        .no-print-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .toggle-compact-btn {{
            background: #475569;
            color: #ffffff;
            border: none;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .toggle-compact-btn:hover {{
            background: #334155;
        }}
        /* Modo Compacto para Forçar Caber em 1 Página */
        body.compact-fit .resume-sheet {{
            padding: 24px 36px;
        }}
        body.compact-fit {{
            font-size: 12px;
            line-height: 1.38;
        }}
        body.compact-fit .candidate-name {{
            font-size: 22px;
            margin-bottom: 1px;
        }}
        body.compact-fit .candidate-role {{
            font-size: 13.5px;
            margin-bottom: 4px;
        }}
        body.compact-fit .contact-bar {{
            font-size: 11px;
            margin-bottom: 14px;
            padding-bottom: 8px;
        }}
        body.compact-fit .section-title {{
            font-size: 13px;
            margin-top: 12px;
            margin-bottom: 5px;
        }}
        body.compact-fit .paragraph {{
            font-size: 11.8px;
            margin-bottom: 6px;
        }}
        body.compact-fit .entry-title {{
            font-size: 12.5px;
            margin-top: 8px;
        }}
        body.compact-fit .entry-meta {{
            font-size: 11px;
            margin-bottom: 3px;
        }}
        body.compact-fit .bullet-item {{
            font-size: 11.5px;
            margin-bottom: 2.5px;
        }}
        body.compact-fit .skills-table th,
        body.compact-fit .skills-table td {{
            padding: 3px 6px;
            font-size: 11px;
        }}
        @page {{
            size: A4 portrait;
            margin: 0;
        }}
        .print-page-layout {{
            width: 100%;
            border-collapse: collapse;
            border: none;
        }}
        .print-page-layout td {{
            padding: 0;
            border: none;
            vertical-align: top;
        }}
        .print-page-header, .print-page-footer {{
            display: none;
        }}
        tr.no-break-after {{
            page-break-after: avoid;
            break-after: avoid;
        }}
        @media print {{
            @page {{
                size: A4 portrait;
                margin: 0; /* Margem zero: o navegador não escreve data, título, URL nem paginação */
            }}
            .print-page-layout {{
                display: table !important;
                width: 100% !important;
                border-collapse: collapse !important;
            }}
            .print-page-header {{
                display: table-header-group !important;
            }}
            .print-page-footer {{
                display: table-footer-group !important;
            }}
            .page-top-spacer {{
                height: 14mm; /* Respiro no topo de TODAS as páginas */
                visibility: hidden;
            }}
            .page-bottom-spacer {{
                height: 16mm; /* Respiro no rodapé de TODAS as páginas */
                visibility: hidden;
            }}
            body.compact-fit .page-top-spacer {{
                height: 9mm;
            }}
            body.compact-fit .page-bottom-spacer {{
                height: 11mm;
            }}
            .print-page-layout tr {{
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }}
            tr.no-break-after {{
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            html, body {{
                background-color: #ffffff !important;
                background: #ffffff !important;
                margin: 0 !important;
                padding: 0 !important;
                font-size: 9.8pt; /* Densidade calibrada para priorizar caber na folha sem cortar */
                line-height: 1.38;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .no-print-bar {{
                display: none !important;
            }}
            .resume-sheet {{
                box-shadow: none !important;
                border: none !important;
                border-radius: 0 !important;
                margin: 0 !important;
                padding: 0 16mm !important; /* Margens laterais */
                max-width: 100% !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }}
            .candidate-name {{
                font-size: 19pt !important;
                margin-bottom: 1px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .candidate-role {{
                font-size: 11.5pt !important;
                margin-bottom: 4px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .contact-bar {{
                font-size: 9pt !important;
                margin-bottom: 10px !important;
                padding-bottom: 6px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .section-title {{
                font-size: 11pt !important;
                border-bottom: 1.2pt solid #0f172a !important;
                color: #0f172a !important;
                margin-top: 11px !important;
                margin-bottom: 4px !important;
                padding-bottom: 2px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .paragraph {{
                font-size: 9.5pt !important;
                margin-bottom: 6px !important;
                line-height: 1.38 !important;
            }}
            .skills-table-container {{
                margin-bottom: 8px !important;
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }}
            .skills-table {{
                font-size: 9.2pt !important;
            }}
            .skills-table th, .skills-table td {{
                padding: 3.5px 6px !important;
            }}
            .skills-table tr {{
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }}
            .entry-title {{
                font-size: 10.2pt !important;
                margin-top: 8px !important;
                margin-bottom: 1px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .entry-meta {{
                font-size: 9.2pt !important;
                margin-bottom: 3px !important;
                page-break-after: avoid !important;
                break-after: avoid !important;
            }}
            .bullet-item {{
                font-size: 9.3pt !important;
                margin-bottom: 2.8px !important;
                line-height: 1.35 !important;
                page-break-inside: avoid !important;
                break-inside: avoid !important;
            }}
            body.compact-fit {{
                font-size: 9.2pt !important;
                line-height: 1.32 !important;
            }}
            body.compact-fit .section-title {{
                margin-top: 8px !important;
                margin-bottom: 3px !important;
                font-size: 10.5pt !important;
            }}
            body.compact-fit .bullet-item {{
                margin-bottom: 2px !important;
                font-size: 8.9pt !important;
            }}
            body.compact-fit .skills-table th, body.compact-fit .skills-table td {{
                padding: 2.5px 5px !important;
                font-size: 8.8pt !important;
            }}
            a {{
                text-decoration: none !important;
                color: inherit !important;
            }}
            a[href]:after {{
                content: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <div class="no-print-info">
            <span>📄 <strong>Folha A4 Pronta para Impressão</strong> (Margens A4 Automáticas)</span>
        </div>
        <div class="no-print-actions">
            <button class="toggle-compact-btn" onclick="document.body.classList.toggle('compact-fit')">📐 Alternar Modo Compacto (1 Folha)</button>
            <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Salvar como PDF</button>
        </div>
    </div>
    <div class="resume-sheet">
        <table class="print-page-layout">
            <thead class="print-page-header">
                <tr>
                    <td>
                        <div class="page-top-spacer"></div>
                    </td>
                </tr>
            </thead>
            <tfoot class="print-page-footer">
                <tr>
                    <td>
                        <div class="page-bottom-spacer"></div>
                    </td>
                </tr>
            </tfoot>
            <tbody>
{body_content}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    return html_template

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

def in_experience_or_projects(body: list) -> bool:
    for item in reversed(body):
        if "section-title" in item:
            return True
    return False

def _inline_format(text: str) -> str:
    # 1. Escapa tags HTML perigosas para prevenir XSS
    safe_text = html.escape(text, quote=True)
    
    # 2. Transforma links Markdown [texto](url) permitindo apenas esquemas seguros (http/https)
    def replace_link(match):
        label = match.group(1)
        url = match.group(2)
        if url.startswith("http://") or url.startswith("https://"):
            return f"<a href='{url}' target='_blank' rel='noopener noreferrer'>{label}</a>"
        return label
        
    safe_text = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", replace_link, safe_text)
    # Remove qualquer link markdown com esquema perigoso (ex: javascript:)
    safe_text = re.sub(r"\[(.+?)\]\((?:javascript|data|vbscript):[^\s)]*\)", r"\1", safe_text, flags=re.IGNORECASE)
    
    # 3. Transforma URLs soltas seguras (sem reescrever links já transformados em <a>)
    def replace_bare_url(match):
        url = match.group(1)
        return f"<a href='{url}' target='_blank' rel='noopener noreferrer'>{url}</a>"
        
    safe_text = re.sub(r"(?<!href=')(https?://[^\s<]+)", replace_bare_url, safe_text)
    
    # 4. Transforma formatações em negrito e itálico
    safe_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe_text)
    safe_text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe_text)
    return safe_text

def _format_contact_item(c: str) -> str:
    c = c.strip()
    # Verifica se o item é um link markdown [texto](url)
    m = re.match(r"^\[(.+?)\]\((.+?)\)$", c)
    if m:
        label = html.escape(m.group(1))
        url = m.group(2).strip()
        if url.startswith("http://") or url.startswith("https://"):
            safe_url = html.escape(url, quote=True)
            return f"<a href='{safe_url}' target='_blank' rel='noopener noreferrer'>{label}</a>"
        return label

    safe_text = html.escape(c)
    if "@" in c and not c.startswith("http"):
        return f"<a href='mailto:{safe_text}'>{safe_text}</a>"
    elif "linkedin.com" in c.lower() or "github.com" in c.lower():
        url = c if (c.startswith("http://") or c.startswith("https://")) else f"https://{c}"
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"
        safe_url = html.escape(url, quote=True)
        return f"<a href='{safe_url}' target='_blank' rel='noopener noreferrer'>{safe_text}</a>"
    return safe_text

