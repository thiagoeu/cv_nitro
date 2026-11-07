"""Template de prompt para auditoria semântica de qualidade (Tier 2) do currículo."""
from langchain_core.prompts import PromptTemplate

QUALITY_REVIEWER_PROMPT = PromptTemplate.from_template(
    "Você é um auditor rigoroso de currículos técnicos de alto padrão e compatibilidade ATS.\n"
    "Avalie o currículo gerado segundo os critérios:\n"
    "1. **Alucinações:** o currículo cita empregos, tecnologias ou ferramentas que NÃO constam no currículo base nem nos READMEs?\n"
    "2. **Idioma:** o currículo está INTEIRAMENTE em {language} (títulos, tabela, bullets, cargos, formação, idiomas)?\n"
    "3. **Layout:** a seção de habilidades é uma tabela Markdown de 2 colunas com linha separadora, "
    "e os bullets seguem o formato `- **Tópico:** ação` (sem colchetes)?\n"
    "4. **Voz Narrativa em 1ª Pessoa:** os bullets de experiência e projetos usam verbos em 1ª pessoa ('Atuo...', 'Desenvolvi...', 'Implementei...') indicando protagonismo e autoria, e NÃO em 3ª pessoa impessoal ('Atua', 'Desenvolveu')?\n\n"
    "Avalie a qualidade ATS:\n"
    "- Atribua um ats_score de 0 a 100 baseado na fidelidade, clareza e densidade das keywords comprovadas (nunca atribua notas altas se o candidato tiver lacunas técnicas não comprovadas na vaga).\n"
    "- Liste em applied_changes de 3 a 5 adequações realizadas em relação ao currículo base.\n"
    "- Forneça em interview_tips de 2 a 3 orientações para entrevista técnica sobre como defender os requisitos da vaga e destacar os projetos reais.\n"
    "- Classifique severity em 'approved' (aprovado), 'minor' (problema pontual em 1 seção específica) ou 'major' (alucinação grave/reescrita total).\n"
    "- Se severity for 'minor', indique em target_section exatamente qual seção deve ser corrigida (ex.: 'HABILIDADES TÉCNICAS', 'PROJETOS EM DESTAQUE', 'RESUMO PROFISSIONAL').\n\n"
    "--- VAGA ALVO ---\n{job_context}\n\n"
    "--- TECNOLOGIAS COMPROVADAS ---\n{verified}\n\n"
    "--- PENDÊNCIAS TÉCNICAS (o candidato NÃO possui; não podem aparecer como experiência) ---\n{gaps}\n\n"
    "--- CURRÍCULO BASE ---\n{base_resume}\n\n"
    "--- READMEs FORNECIDOS ---\n{portfolio_context}\n\n"
    "--- CURRÍCULO GERADO (Para revisão) ---\n{generated}\n\n"
    "Retorne a análise estruturada."
)

