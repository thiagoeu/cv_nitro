import io
import os
from typing import Union, BinaryIO
from pypdf import PdfReader
import docx

def extract_text_from_file(file_input: Union[str, BinaryIO, any], filename: str = None) -> str:
    """
    Extrai texto a partir de um arquivo nos formatos PDF, DOCX, MD ou TXT.
    
    file_input pode ser um caminho no sistema de arquivos, um objeto BytesIO 
    ou um UploadedFile do Streamlit.
    """
    if filename is None:
        if isinstance(file_input, str):
            filename = os.path.basename(file_input)
        elif hasattr(file_input, "name"):
            filename = file_input.name
        else:
            filename = ""

    ext = os.path.splitext(filename)[1].lower()

    # Prepara o stream em memória se for caminho de arquivo
    if isinstance(file_input, str):
        with open(file_input, "rb") as f:
            stream = io.BytesIO(f.read())
    elif hasattr(file_input, "read"):
        content = file_input.read()
        # Se for UploadedFile do Streamlit, redefinir ponteiro se possível
        if hasattr(file_input, "seek"):
            file_input.seek(0)
        stream = io.BytesIO(content)
    else:
        raise ValueError("Entrada de arquivo inválida.")

    extracted_text = ""

    if ext == ".pdf":
        try:
            reader = PdfReader(stream)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            extracted_text = "\n\n".join(pages_text)
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto do PDF ({filename}): {e}")

    elif ext in [".docx", ".doc"]:
        try:
            doc = docx.Document(stream)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            extracted_text = "\n\n".join(paragraphs)
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto do DOCX ({filename}): {e}")

    elif ext in [".md", ".markdown", ".txt", ""]:
        try:
            raw = stream.getvalue()
            try:
                extracted_text = raw.decode("utf-8")
            except UnicodeDecodeError:
                extracted_text = raw.decode("latin-1")
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair texto do arquivo ({filename}): {e}")

    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}. Formatos suportados: .pdf, .docx, .md, .txt")

    return extracted_text.strip()
