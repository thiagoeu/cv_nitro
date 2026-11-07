"""Templates de prompt para geração de currículo, patch cirúrgico de seção e carta de apresentação."""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate


def build_resume_system_prompt(labels: dict, verified_str: str, gaps_str: str) -> str:
    """Constrói o system prompt canônico de geração do currículo ATS no idioma da vaga."""
    return f"""Você é um especialista em recrutamento executivo de tecnologia e sistemas ATS.
Sua missão é reescrever o currículo base em Markdown de ALTA FIDELIDADE e PADRONIZAÇÃO EXECUTIVA, escrito inteiramente em {labels['name']}.

ESTRUTURA OBRIGATÓRIA (substitua cada <marcador> pelo conteúdo real; nunca escreva os sinais < >, colchetes ou o nome do marcador):

# <Nome completo do candidato>
### <Cargo profissional REAL do candidato baseado no currículo base (ex.: 'Desenvolvedor Full Stack' ou 'Engenheiro de Software'). ATENÇÃO: NUNCA assuma um título de cargo de tecnologias que você NÃO domina (ex.: se a vaga pede Java mas o candidato não possui Java em seu histórico, NUNCA coloque 'Desenvolvedor Java'; mantenha a identidade profissional real como 'Desenvolvedor Full Stack')>
<Cidade, UF / País> | <Email> | <LinkedIn> | <GitHub>

## {labels['summary']}
<Um único parágrafo denso destacando senioridade, stack principal comprovada do candidato, escala dos projetos e diferenciais técnicos reais. Seja 100% honesto: NUNCA declare domínio, experiência ou proficiência em tecnologias que constem na lista de pendências técnicas>

## {labels['skills']}
{labels['table_header']}
| :--- | :--- |
| **<Categoria>** | <tecnologias e conceitos separados por vírgula> |

(Uma linha por categoria, ex.: {labels['categories']}. Adapte as categorias ao candidato, sempre com 2 colunas e a linha separadora.)

## {labels['experience']}
### <Empresa / Órgão — Projeto>
*<Cargo> | <Período> | <Localidade (Remoto ou Presencial)>*
- **<Tópico de impacto>:** <verbo de ação em 1ª pessoa + escopo + resultado mensurável ou de escala>

(3 a 5 bullets por experiência, cobrindo impacto, back-end/arquitetura, front-end, dados/integrações e processos, quando aplicável. Use SEMPRE verbos em 1ª pessoa indicando autoria própria: no cargo atual use o presente como 'Atuo...', 'Construo...', 'Desenvolvo...', 'Lidero...'; em cargos passados use o pretérito como 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Otimizei...'. NUNCA use a 3ª pessoa como 'Atua', 'Constrói', 'Desenvolveu', 'Implementou'.)

## {labels['projects']}
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação em 1ª pessoa, ex: 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Projetei...'>
- **{labels['repo']}:** <URL do repositório no GitHub>

(Na seção de projetos, use EXCLUSIVAMENTE os projetos fornecidos no bloco 'PORTFÓLIO GITHUB' com seus nomes e URLs exatas. NUNCA cite projetos do currículo base que não constem no PORTFÓLIO GITHUB.)

## {labels['education']}
### <Grau e curso>
*<Instituição> | <Ano de conclusão / previsão>*

## {labels['certifications']}
- **<Curso / certificação>:** <Instituição> (<Ano>)

## {labels['languages']}
<Idioma>: <Nível> | <Idioma>: <Nível>

REGRAS CRÍTICAS:
1. IDIOMA: todo o currículo DEVE estar em {labels['name']}. Se o currículo base estiver em outro idioma, TRADUZA integralmente: resumo, cargos, bullets, tópicos, cabeçalho e categorias da tabela, formação, certificações, nomes dos idiomas e níveis. Mantenha como no original apenas nomes de pessoas, empresas, instituições, projetos e tecnologias.
2. BULLETS: sempre `- **Tópico:** ação`. Não use "●", "•" nem colchetes.
3. TABELA: a seção de habilidades é SEMPRE a tabela Markdown de 2 colunas acima, com a linha separadora `| :--- | :--- |`.
4. ATS & EQUIVALÊNCIAS: integre naturalmente as palavras-chave comprovadas da vaga nas experiências e habilidades.
5. TRAVA FACTUAL ANTI-ALUCINAÇÃO (WHITELIST E TOTAL HONESTIDADE):
   - CARGO E IDENTIDADE: Mantenha sempre o cargo profissional REAL do candidato baseado no histórico comprovado. Jamais invente ou intitule o candidato com uma tecnologia que ele não possui (ex.: se a vaga pede Java mas o candidato é Full Stack em Node/React/Go, declare 'Desenvolvedor Full Stack', NUNCA 'Desenvolvedor Java').
   - TECNOLOGIAS COMPROVADAS PERMITIDAS: {verified_str}.
   - PENDÊNCIAS TÉCNICAS DA VAGA (PROIBIDAS NO CURRÍCULO): É TERMINANTEMENTE PROIBIDO inventar ou atribuir ao candidato as seguintes tecnologias: {gaps_str}. NUNCA as coloque no título, no resumo, na tabela de habilidades nem nas experiências como se o candidato as dominasse. Elas são lacunas e serão abordadas de forma transparente na carta de apresentação e roteiro de entrevista.
   - SOURCING ESTRITO DE PROJETOS: Na seção de projetos em destaque, cite apenas repositórios do PORTFÓLIO GITHUB fornecido.
6. VOZ NARRATIVA E AUTORIA EM 1ª PESSOA: Todos os bullets de experiência e projetos DEVEM ser redigidos em PRIMEIRA PESSOA ('eu fiz'), transmitindo protagonismo, proatividade e sentimento de dono (ownership).
   - Cargo/experiência atual (presente): conjugue na 1ª pessoa do presente (ex.: "Atuo no desenvolvimento...", "Construo e mantenho APIs...", "Desenvolvo testes...", "Lidero...").
   - Cargos passados e projetos (passado): conjugue na 1ª pessoa do pretérito perfeito (ex.: "Desenvolvi...", "Implementei...", "Estruturei...", "Configurei...", "Solucionei...").
   - NUNCA use verbos na 3ª pessoa (ex.: "Atua", "Constrói", "Desenvolveu", "Implementou"), pois soa impessoal e retira a autoria do candidato.
7. Retorne APENAS o Markdown do currículo, sem comentários e sem cercas de código (```)."""


def build_resume_user_messages(
    system_prompt: str,
    base_resume: str,
    job_desc: str,
    verified_str: str,
    gaps_str: str,
    portfolio: str,
    feedback: str = "",
) -> list:
    """Monta a lista de mensagens (System + Human) ordenada para máximo aproveitamento de Prompt Caching."""
    feedback_text = (
        f"\n\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. "
        "Ajuste o currículo rigorosamente conforme esse feedback."
        if feedback else ""
    )
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}"),
        HumanMessage(
            content=(
                f"--- VAGA ALVO ---\n{job_desc}\n\n"
                f"--- TECNOLOGIAS COMPROVADAS (PERMITIDAS NO CURRÍCULO) ---\n{verified_str}\n\n"
                f"--- PENDÊNCIAS TÉCNICAS DA VAGA (NÃO INVENTAR NO CURRÍCULO) ---\n{gaps_str}\n\n"
                f"--- PORTFÓLIO GITHUB (USAR APENAS ESSES EM PROJETOS) ---\n{portfolio}{feedback_text}"
            )
        ),
    ]


SECTION_PATCH_PROMPT = PromptTemplate.from_template(
    "Você é um especialista em recrutamento técnico.\n"
    "Sua tarefa é reescrever EXCLUSIVAMENTE a seção '{target_section}' do currículo abaixo em Markdown.\n\n"
    "DIRETRIZ DE REVISÃO / AJUSTE:\n"
    "{instruction}\n\n"
    "CURRÍCULO ATUAL:\n"
    "{current_resume}\n\n"
    "REGRAS:\n"
    "1. Escreva inteiramente em {language}.\n"
    "2. Se for seção de experiência ou projetos, use OBRIGATORIAMENTE verbos em 1ª PESSOA indicando autoria ('Atuo...', 'Desenvolvi...', 'Implementei...'), nunca na 3ª pessoa ('Atua', 'Desenvolveu').\n"
    "3. Retorne APENAS o bloco Markdown correspondente a esta seção, começando com '## {target_section}'.\n"
    "4. Não inclua comentários nem cercas de código (```)."
)


def build_cover_letter_prompts(
    lang_name: str,
    job_desc: str,
    generated_resume: str,
    repos_summary: str,
    verified_str: str,
    gaps_str: str,
) -> tuple[str, str]:
    """Constrói os prompts (system_prompt, user_prompt) da carta de apresentação."""
    system_prompt = (
        "Você é um especialista sênior em redação de cartas de apresentação (Cover Letters) e aconselhamento de carreira.\n"
        f"Escreva uma Cover Letter profissional, elegante e persuasiva inteiramente em {lang_name}, adaptada para a vaga descrita.\n\n"
        "Diretrizes:\n"
        "1. **Abertura**: Saudação formal ao time de recrutamento/gerente de contratação e apresentação com entusiasmo pela vaga.\n"
        "2. **Conexão Técnica & Experiência**: Destaque as principais realizações do candidato pertinentes à vaga, citando experiência prática e projetos reais.\n"
        "3. **Fit Cultural & Valor**: Mostre compreensão dos objetivos da empresa e como o candidato resolverá os desafios propostos.\n"
        "4. **Fechamento**: Conclusão cordial solicitando uma entrevista/conversa técnica.\n"
        "5. **Alinhamento Rigoroso**: NÃO invente informações que não estejam presentes no currículo do candidato.\n"
        "6. **Pendências técnicas**: as tecnologias listadas como pendências o candidato NÃO domina. Cite-as no máximo como interesse "
        "ou disposição para aprender, nunca como experiência, domínio ou projeto realizado.\n"
        "- Retorne APENAS o texto da carta em Markdown limpo, sem cercas de código (```)."
    )
    user_prompt = (
        f"--- VAGA ---\n{job_desc}\n\n"
        f"--- CURRÍCULO DO CANDIDATO ---\n{generated_resume}\n\n"
        f"--- PROJETOS DESTACADOS GITHUB ---\n{repos_summary}\n\n"
        f"--- TECNOLOGIAS COMPROVADAS ---\n{verified_str}\n\n"
        f"--- PENDÊNCIAS TÉCNICAS (não reivindicar experiência) ---\n{gaps_str}"
    )
    return system_prompt, user_prompt

