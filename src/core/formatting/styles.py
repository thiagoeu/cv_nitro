"""Folha de estilo CSS A4 (@media print e modo compacto) e template HTML do currículo."""
import html


def build_a4_html_document(doc_title: str, body_content: str) -> str:
    """Monta o documento HTML completo com folha de estilo A4 e barra de controle de impressão."""
    return f"""<!DOCTYPE html>
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
            </thead>
            <tbody>
{body_content}
            </tbody>
        </table>
    </div>
</body>
</html>"""

