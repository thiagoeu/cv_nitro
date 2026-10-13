import re
from typing import Optional

def format_resume_to_html(markdown_content: str, title: Optional[str] = None) -> str:
    """
    Converte o currículo em Markdown no layout canônico para um documento HTML estilizado,
    com visual profissional em folha A4 e regras de impressão (@media print) para PDF.
    """
    if not markdown_content:
        return "<html><body><p>Nenhum conteúdo para exibir.</p></body></html>"

    lines = markdown_content.strip().split("\n")
    html_body = []
    
    in_table = False
    table_rows = []
    
    # Extrai o título se não foi passado
    doc_title = title or "Currículo Profissional"

    for raw_line in lines:
        line = raw_line.strip()
        
        # Linhas de tabela
        if line.startswith("|") and line.endswith("|"):
            # Ignora linha divisória (| :--- | :--- |)
            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2:
                table_rows.append(cells)
                in_table = True
            continue
        else:
            if in_table and table_rows:
                # Fecha tabela acumulada
                html_body.append("<div class='skills-table-container'><table class='skills-table'>")
                for r_idx, row in enumerate(table_rows):
                    tag = "th" if r_idx == 0 and ("Categoria" in row[0] or "Category" in row[0]) else "td"
                    html_body.append("<tr>")
                    html_body.append(f"<{tag} class='col-cat'>{_inline_format(row[0])}</{tag}>")
                    html_body.append(f"<{tag} class='col-tech'>{_inline_format(row[1])}</{tag}>")
                    html_body.append("</tr>")
                html_body.append("</table></div>")
                table_rows = []
                in_table = False

        if not line:
            continue

        # Header H1: Nome do Candidato
        if line.startswith("# "):
            name = line[2:].strip()
            doc_title = name
            html_body.append(f"<h1 class='candidate-name'>{name}</h1>")
            continue

        # Subtítulo H3: Cargo Alvo
        if line.startswith("### ") and not in_experience_or_projects(html_body):
            role = line[4:].strip()
            html_body.append(f"<div class='candidate-role'>{role}</div>")
            continue

        # Linha de contatos (Cidade | Email | etc.)
        if "|" in line and not line.startswith("|") and ("@" in line or "github" in line.lower() or "linkedin" in line.lower() or len(html_body) <= 3):
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
            html_body.append(f"<h2 class='section-title'>{sec_name}</h2>")
            continue

        # Subseções H3 dentro de experiência/projetos
        if line.startswith("### "):
            sub_title = line[4:].strip()
            html_body.append(f"<h3 class='entry-title'>{_inline_format(sub_title)}</h3>")
            continue

        # Subtítulo em itálico (Cargo | Período | Local)
        if (line.startswith("*") and line.endswith("*")) or (line.startswith("_") and line.endswith("_")):
            meta_info = line.strip("*_").strip()
            html_body.append(f"<div class='entry-meta'>{meta_info}</div>")
            continue

        # Bullet points de impacto (- ● **Tópico**: ou - • **Tópico**: ou - **Tópico**:)
        if line.startswith("-") or line.startswith("*") or line.startswith("●") or line.startswith("•"):
            # Limpa prefixo de lista
            content = re.sub(r"^[-*●•\s]+", "", line).strip()
            # Remove eventual ● interno
            content = re.sub(r"^[●•\s]+", "", content).strip()
            formatted_content = _inline_format(content)
            html_body.append(f"<div class='bullet-item'><span class='bullet-point'>●</span> <div class='bullet-text'>{formatted_content}</div></div>")
            continue

        # Parágrafos normais (ex: Resumo Profissional)
        html_body.append(f"<p class='paragraph'>{_inline_format(line)}</p>")

    if in_table and table_rows:
        html_body.append("<div class='skills-table-container'><table class='skills-table'>")
        for r_idx, row in enumerate(table_rows):
            tag = "th" if r_idx == 0 and ("Categoria" in row[0] or "Category" in row[0]) else "td"
            html_body.append("<tr>")
            html_body.append(f"<{tag} class='col-cat'>{_inline_format(row[0])}</{tag}>")
            html_body.append(f"<{tag} class='col-tech'>{_inline_format(row[1])}</{tag}>")
            html_body.append("</tr>")
        html_body.append("</table></div>")

    body_content = "\n".join(html_body)

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{doc_title}</title>
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
            margin: 0 auto 15px auto;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }}
        .print-btn {{
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: background 0.2s;
        }}
        .print-btn:hover {{
            background-color: #1d4ed8;
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
        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
                font-size: 11pt;
            }}
            .no-print-bar {{
                display: none !important;
            }}
            .resume-sheet {{
                box-shadow: none;
                border-radius: 0;
                padding: 0;
                max-width: 100%;
            }}
            .section-title {{
                border-bottom: 1.5pt solid #000;
                color: #000;
                page-break-after: avoid;
            }}
            .bullet-item {{
                page-break-inside: avoid;
            }}
            @page {{
                size: A4;
                margin: 15mm 18mm;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Salvar como PDF</button>
    </div>
    <div class="resume-sheet">
{body_content}
    </div>
</body>
</html>"""
    return html_template

def in_experience_or_projects(body: list) -> bool:
    for item in reversed(body):
        if "section-title" in item:
            return True
    return False

def _inline_format(text: str) -> str:
    # Negrito **texto**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Itálico *texto*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Links markdown [texto](url)
    text = re.sub(r"\[(.+?)\]\((https?://[^\s)]+)\)", r"<a href='\2' target='_blank'>\1</a>", text)
    # URLs soltas https://...
    text = re.sub(r"(?<!href=')(https?://[^\s<]+)", r"<a href='\1' target='_blank'>\1</a>", text)
    return text

def _format_contact_item(c: str) -> str:
    c = c.strip()
    if "@" in c and not c.startswith("http"):
        return f"<a href='mailto:{c}'>{c}</a>"
    elif "linkedin.com" in c.lower() or "github.com" in c.lower():
        url = c if c.startswith("http") else f"https://{c}"
        return f"<a href='{url}' target='_blank'>{c}</a>"
    return c
