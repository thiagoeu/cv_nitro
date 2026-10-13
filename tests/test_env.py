from src.core import config

print("Testando leitura de variáveis de ambiente:")
print(f"GEMINI_API_KEY: {'Configurada' if config.GEMINI_API_KEY else 'NÃO Configurada'}")
print(f"GITHUB_TOKEN: {'Configurada' if config.GITHUB_TOKEN else 'NÃO Configurada'}")
