import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Usado quando o modelo principal responde 503 (sobrecarga). Vazio desativa.
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    
if not GITHUB_TOKEN:
    print("INFO: GITHUB_TOKEN não encontrada (opcional, pode resultar em limites de API mais rigorosos).")

