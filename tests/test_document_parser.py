import os
import io
import pytest
from src.core.document_parser import extract_text_from_file

def test_extract_text_markdown_txt():
    content = "# Curriculo\nDesenvolvedor Python com 5 anos de experiência."
    stream = io.BytesIO(content.encode("utf-8"))
    stream.name = "curriculo.md"
    extracted = extract_text_from_file(stream)
    assert "Desenvolvedor Python" in extracted
    assert "# Curriculo" in extracted

def test_extract_text_docx():
    import docx
    doc = docx.Document()
    doc.add_heading("Currículo João Silva", 0)
    doc.add_paragraph("Engenheiro de Software com foco em Python e IA.")
    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)
    stream.name = "curriculo.docx"
    
    extracted = extract_text_from_file(stream)
    assert "Currículo João Silva" in extracted
    assert "Engenheiro de Software" in extracted

def test_extract_text_pdf():
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    stream = io.BytesIO()
    writer.write(stream)
    stream.seek(0)
    stream.name = "curriculo.pdf"
    
    # Testa que não quebra ao ler pdf (mesmo que página em branco retorne vazio)
    extracted = extract_text_from_file(stream)
    assert isinstance(extracted, str)
