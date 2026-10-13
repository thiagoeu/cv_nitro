import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    
if not GITHUB_TOKEN:
    print("INFO: GITHUB_TOKEN não encontrada (opcional, pode resultar em limites de API mais rigorosos).")
