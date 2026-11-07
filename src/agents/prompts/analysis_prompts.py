"""Templates de prompt para os agentes de análise de vaga e mapeamento semântico de competências."""
from langchain_core.prompts import PromptTemplate

JOB_ANALYZER_PROMPT = PromptTemplate.from_template(
    "Você é um recrutador especialista. Analise a seguinte vaga de emprego "
    "e extraia as principais tecnologias, palavras-chave comportamentais/conceituais "
    "e identifique o idioma em que a vaga está escrita. Ignore textos de interface do site "
    "de vagas (ex.: 'Sobre a vaga', 'Candidatar-se') ao decidir o idioma. "
    "Escreva também um resumo enxuto da vaga, que substituirá o texto original nas próximas etapas.\n\n"
    "Vaga:\n{job_description}"
)

COMPETENCY_PROMPT = PromptTemplate.from_template(
    "Você é um especialista em auditoria técnica de competências e compatibilidade de vagas de tecnologia.\n"
    "Sua missão é cruzar as tecnologias exigidas pela vaga com o perfil real do candidato (currículo base e portfólio no GitHub) "
    "e classificar com inteligência semântica e honestidade estrita:\n\n"
    "DIRETRIZES DE AUDITORIA:\n"
    "1. **Reconhecimento Semântico Amplo:** Reconheça ferramentas, frameworks, ecossistemas e sinônimos legítimos de mercado. "
    "Por exemplo: Expo comprova React Native; NestJS e Express comprovam Node.js; PostgreSQL, MySQL e SQLite comprovam SQL; "
    "TypeORM e Prisma comprovam ORM/bancos relacionais; Docker Compose comprova Docker; RAG, Ollama e LLMs comprovam IA Generativa; etc.\n"
    "2. **HONESTIDADE E TRAVA FACTUAL (NÃO INVENTE):** Se o candidato NÃO possui experiência nem projetos com a tecnologia "
    "(ex.: Java, C#, Flutter, Kubernetes) e ela não é respaldada por nenhuma ferramenta equivalente do perfil, "
    "coloque-a OBRIGATORIAMENTE em 'unmatched_gaps'. Jamais suponha competências sem evidência textual ou prática!\n\n"
    "--- VAGA ALVO ---\n"
    "Cargo: {job_title}\n"
    "Tecnologias exigidas: {job_technologies}\n\n"
    "--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}\n\n"
    "--- REPOSITÓRIOS GITHUB DO CANDIDATO ---\n{github_repos_summary}\n\n"
    "Retorne a análise estruturada."
)

