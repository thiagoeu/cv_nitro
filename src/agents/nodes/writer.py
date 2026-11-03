"""Agentes de redação: currículo completo, refinamento de uma seção e carta de apresentação."""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from src.agents.shared import llm
from src.agents.nodes.analysis import job_context
from src.agents.nodes.github import portfolio_context
from src.agents.shared.sections import LABELS, splice_markdown_section, unfilled_placeholders
from src.core import competency_matcher as competency_matcher_core

def resume_generator(state: dict) -> dict:
    """
    Gera um novo currículo em Markdown com formatação de alta fidelidade e aderência ATS,
    no idioma da vaga (traduzindo o currículo base), com tabela de habilidades e bullets de impacto.
    Uma única chamada: os extratos higienizados dos READMEs (top 3) vão direto no prompt.
    """
    base_resume = state.get("base_resume_md", "")
    job_desc = job_context(state)
    feedback = state.get("reviewer_feedback", "")
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])

    feedback_text = f"\n\nATENÇÃO! O revisor rejeitou a versão anterior pelo seguinte motivo: {feedback}. Ajuste o currículo rigorosamente conforme esse feedback." if feedback else ""
    portfolio = portfolio_context(state, 1200) or "Nenhum repositório do GitHub fornecido."

    verified_techs = state.get("verified_technologies")
    gaps = state.get("unmatched_gaps")
    if verified_techs is None or gaps is None:
        classified = competency_matcher_core.classify_competencies(
            state.get("job_technologies", []),
            base_resume,
            state.get("github_repos", []) or state.get("raw_github_repos", []) or [],
            state.get("github_readmes")
        )
        verified_techs = classified["verified_technologies"]
        gaps = classified["unmatched_gaps"]

    verified_str = ", ".join(verified_techs) if verified_techs else "Utilize apenas as tecnologias do currículo base."
    gaps_str = ", ".join(gaps) if gaps else "Nenhuma pendência identificada."

    # 1. Prefixo estático imutável: Regras ATS e Layouts (máximo reuso de Prompt Caching)
    system_prompt = f"""Você é um especialista em recrutamento executivo de tecnologia e sistemas ATS.
Sua missão é reescrever o currículo base em Markdown de ALTA FIDELIDADE e PADRONIZAÇÃO EXECUTIVA, escrito inteiramente em {L['name']}.

ESTRUTURA OBRIGATÓRIA (substitua cada <marcador> pelo conteúdo real; nunca escreva os sinais < >, colchetes ou o nome do marcador):

# <Nome completo do candidato>
### <Cargo profissional REAL do candidato baseado no currículo base (ex.: 'Desenvolvedor Full Stack' ou 'Engenheiro de Software'). ATENÇÃO: NUNCA assuma um título de cargo de tecnologias que você NÃO domina (ex.: se a vaga pede Java mas o candidato não possui Java em seu histórico, NUNCA coloque 'Desenvolvedor Java'; mantenha a identidade profissional real como 'Desenvolvedor Full Stack')>
<Cidade, UF / País> | <Email> | <LinkedIn> | <GitHub>

## {L['summary']}
<Um único parágrafo denso destacando senioridade, stack principal comprovada do candidato, escala dos projetos e diferenciais técnicos reais. Seja 100% honesto: NUNCA declare domínio, experiência ou proficiência em tecnologias que constem na lista de pendências técnicas>

## {L['skills']}
{L['table_header']}
| :--- | :--- |
| **<Categoria>** | <tecnologias e conceitos separados por vírgula> |

(Uma linha por categoria, ex.: {L['categories']}. Adapte as categorias ao candidato, sempre com 2 colunas e a linha separadora.)

## {L['experience']}
### <Empresa / Órgão — Projeto>
*<Cargo> | <Período> | <Localidade (Remoto ou Presencial)>*
- **<Tópico de impacto>:** <verbo de ação em 1ª pessoa + escopo + resultado mensurável ou de escala>

(3 a 5 bullets por experiência, cobrindo impacto, back-end/arquitetura, front-end, dados/integrações e processos, quando aplicável. Use SEMPRE verbos em 1ª pessoa indicando autoria própria: no cargo atual use o presente como 'Atuo...', 'Construo...', 'Desenvolvo...', 'Lidero...'; em cargos passados use o pretérito como 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Otimizei...'. NUNCA use a 3ª pessoa como 'Atua', 'Constrói', 'Desenvolveu', 'Implementou'.)

## {L['projects']}
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação em 1ª pessoa, ex: 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Projetei...'>
- **{L['repo']}:** <URL do repositório no GitHub>

(Na seção de projetos, use EXCLUSIVAMENTE os projetos fornecidos no bloco 'PORTFÓLIO GITHUB' com seus nomes e URLs exatas. NUNCA cite projetos do currículo base que não constem no PORTFÓLIO GITHUB.)

## {L['education']}
### <Grau e curso>
*<Instituição> | <Ano de conclusão / previsão>*

## {L['certifications']}
- **<Curso / certificação>:** <Instituição> (<Ano>)

## {L['languages']}
<Idioma>: <Nível> | <Idioma>: <Nível>

REGRAS CRÍTICAS:
1. IDIOMA: todo o currículo DEVE estar em {L['name']}. Se o currículo base estiver em outro idioma, TRADUZA integralmente: resumo, cargos, bullets, tópicos, cabeçalho e categorias da tabela, formação, certificações, nomes dos idiomas e níveis. Mantenha como no original apenas nomes de pessoas, empresas, instituições, projetos e tecnologias.
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

    # Prefixo estável primeiro (regras -> currículo base) para aproveitar o cache implícito de prompt
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}"),
        HumanMessage(
            content=(
                f"--- VAGA ALVO ---\n{job_desc}\n\n"
                f"--- TECNOLOGIAS COMPROVADAS (PERMITIDAS NO CURRÍCULO) ---\n{verified_str}\n\n"
                f"--- PENDÊNCIAS TÉCNICAS DA VAGA (NÃO INVENTAR NO CURRÍCULO) ---\n{gaps_str}\n\n"
                f"--- PORTFÓLIO GITHUB (USAR APENAS ESSES EM PROJETOS) ---\n{portfolio}{feedback_text}"
            )
        )
    ]
    response = llm.invoke_tracked(llm.chat_model(temperature=0.2, thinking_level=None), messages,
                               f"{system_prompt}\n{base_resume}\n{job_desc}\n{portfolio}")
    generated_text = llm.response_text(response)
    return {
        "generated_resume_md": generated_text,
        "generation_truncated": llm.is_truncated(response),
        "agent_trace": [{
            "agent": "resume_generator",
            "step": "Redação Executiva ATS",
            "detail": f"Currículo gerado integralmente em {L['name']} com tabela de habilidades e verbos em 1ª pessoa.",
            "status": "success"
        }]
    }


def section_patcher(state: dict) -> dict:
    """
    Refinamento cirúrgico de seção (Delta Section Patching):
    Reescreve exclusivamente a seção rejeitada pelo quality_reviewer (falha 'minor'),
    economizando mais de 80% dos tokens de saída em relação a uma regeneração completa.
    """
    current_resume = state.get("generated_resume_md", "") or ""
    target_section = state.get("patch_section")
    instruction = state.get("patch_instruction") or state.get("reviewer_feedback") or "Ajuste a seção conforme as diretrizes."
    L = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])

    if not target_section or not current_resume:
        return {"generated_resume_md": current_resume}

    prompt = PromptTemplate.from_template(
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

    try:
        formatted_prompt = prompt.format(
            target_section=target_section,
            instruction=instruction,
            current_resume=current_resume,
            language=L["name"]
        )
        response = llm.invoke_tracked(llm.chat_model(temperature=0.2, thinking_level="low"), formatted_prompt, formatted_prompt)
        patched_section_md = llm.response_text(response)
        updated_resume = splice_markdown_section(current_resume, target_section, patched_section_md)
        return {
            "generated_resume_md": updated_resume,
            # O patch troca uma seção só: um truncamento anterior do gerador continua valendo
            "generation_truncated": bool(state.get("generation_truncated")) or llm.is_truncated(response),
            "agent_trace": [{
                "agent": "section_patcher",
                "step": "Refinamento Cirúrgico de Seção",
                "detail": f"Seção '{target_section}' reescrita cirurgicamente e reenxertada sem refazer o currículo inteiro.",
                "status": "success"
            }]
        }
    except Exception as e:
        print(f"Erro no section_patcher: {e}")
        return {
            "generated_resume_md": current_resume,
            "errors": [f"Falha no patch cirúrgico: {e}"],
            "agent_trace": [{
                "agent": "section_patcher",
                "step": "Refinamento Cirúrgico de Seção",
                "detail": f"Falha no patch cirúrgico: {e}",
                "status": "error"
            }]
        }


def cover_letter_generator(state: dict) -> dict:
    """
    Gera uma Cover Letter (Carta de Apresentação) personalizada, convincente e alinhada
    com a vaga e o portfólio GitHub, escrita no mesmo idioma da vaga.
    """
    project_items = []
    for r in (state.get("github_repos") or [])[:3]:
        name = r.get("name")
        if not name:
            continue
        lang = r.get("language") or "Multi-stack"
        desc = (r.get("description") or "").strip()
        if desc:
            desc_short = desc[:110] + ("..." if len(desc) > 110 else "")
            project_items.append(f"- **{name}** ({lang}): {desc_short}")
        else:
            project_items.append(f"- **{name}** ({lang})")
    repos_summary = "\n".join(project_items) if project_items else "Nenhum repositório específico."
    lang_name = LABELS.get(state.get("job_language") or "pt", LABELS["pt"])["name"]

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
        f"--- VAGA ---\n{job_context(state)}\n\n"
        f"--- CURRÍCULO DO CANDIDATO ---\n{state.get('generated_resume_md', '')}\n\n"
        f"--- PROJETOS DESTACADOS GITHUB ---\n{repos_summary}\n\n"
        f"--- TECNOLOGIAS COMPROVADAS ---\n{', '.join(state.get('verified_technologies') or []) or 'Nenhuma informada.'}\n\n"
        f"--- PENDÊNCIAS TÉCNICAS (não reivindicar experiência) ---\n{', '.join(state.get('unmatched_gaps') or []) or 'Nenhuma.'}"
    )

    try:
        response = llm.invoke_tracked(llm.chat_model(temperature=0.3), [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ], f"{system_prompt}\n{user_prompt}")
        letter = llm.response_text(response)
        unfilled = [m.group() for m in unfilled_placeholders(letter)]
        return {
            "generated_cover_letter_md": letter,
            "errors": [f"A carta de apresentação tem marcadores não preenchidos ({', '.join(unfilled[:3])}); revise antes de enviar."] if unfilled else [],
            "agent_trace": [{
                "agent": "cover_letter_generator",
                "step": "Redação da Carta de Apresentação",
                "detail": f"Carta de apresentação em 4 atos estruturada em {lang_name} com base nos projetos do portfólio.",
                "status": "success"
            }]
        }
    except Exception as e:
        print(f"Erro no Cover Letter Generator: {e}")
        return {
            "generated_cover_letter_md": "",
            "errors": [f"Carta de apresentação não foi gerada ({e})."],
            "agent_trace": [{
                "agent": "cover_letter_generator",
                "step": "Redação da Carta de Apresentação",
                "detail": f"Carta não gerada devido a falha na API ({e}).",
                "status": "warning"
            }]
        }
