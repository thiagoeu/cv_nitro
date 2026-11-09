"""Templates de prompt para otimização geral de currículo (sem vaga específica)."""
from langchain_core.messages import HumanMessage, SystemMessage


def build_general_resume_system_prompt(labels: dict, target_focus: str = "") -> str:
    """Constrói o system prompt para geração de currículo geral de alto impacto no padrão A4."""
    focus_instruction = (
        f"Direcione o posicionamento executivo para o foco/cargo: '{target_focus}' (desde que compatível com a trajetória real do candidato)."
        if target_focus.strip()
        else "Posicione o candidato pelo seu cargo e senioridade reais comprovados no currículo base e portfólio."
    )
    return f"""Você é um especialista em recrutamento executivo de tecnologia, engenharia de software e sistemas ATS.
Sua missão é transformar o currículo base do candidato (e seu portfólio do GitHub, quando disponível) em um CURRÍCULO GERAL DE ALTO IMPACTO em Markdown de ALTA FIDELIDADE e PADRONIZAÇÃO EXECUTIVA, escrito inteiramente em {labels['name']}, sem depender de uma vaga específica.

DIRETRIZ DE POSICIONAMENTO:
{focus_instruction}
Destaque de forma clara, rica e bem categorizada TODAS as tecnologias, linguagens, frameworks, bancos de dados, ferramentas de nuvem/DevOps e arquiteturas relevantes que estejam comprovadas no currículo base e nos repositórios do GitHub do candidato.

ESTRUTURA OBRIGATÓRIA (substitua cada <marcador> pelo conteúdo real; nunca escreva os sinais < >, colchetes ou o nome do marcador):

# <Nome completo do candidato>
### <Cargo profissional REAL do candidato baseado no currículo base (ex.: 'Engenheiro de Software Full Stack', 'Desenvolvedor Back-end', etc.)>
<Cidade, UF / País> | <Email> | <LinkedIn> | <GitHub>

## {labels['summary']}
<Um único parágrafo denso e executivo destacando senioridade, principais stacks tecnológicas comprovadas, arquitetura de sistemas, escala dos projetos entregues e diferenciais técnicos reais do candidato.>

## {labels['skills']}
{labels['table_header']}
| :--- | :--- |
| **<Categoria>** | <tecnologias e conceitos comprovados separados por vírgula> |

(Uma linha por categoria, ex.: {labels['categories']}. Agrupe todas as tecnologias relevantes do candidato em categorias lógicas, sempre com 2 colunas e a linha separadora.)

## {labels['experience']}
### <Empresa / Órgão — Projeto>
*<Cargo> | <Período> | <Localidade (Remoto ou Presencial)>*
- **<Tópico de impacto>:** <verbo de ação em 1ª pessoa + tecnologias aplicadas + escopo + resultado ou impacto técnico>

(3 a 5 bullets por experiência, destacando as tecnologias relevantes utilizadas em cada entrega. Use SEMPRE verbos em 1ª pessoa indicando autoria própria: no cargo atual use o presente como 'Atuo...', 'Construo...', 'Desenvolvo...', 'Lidero...'; em cargos passados use o pretérito como 'Desenvolvi...', 'Implementei...', 'Estruturei...', 'Otimizei...'. NUNCA use a 3ª pessoa.)

## {labels['projects']}
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação em 1ª pessoa ('Desenvolvi...', 'Implementei...', 'Estruturei...', 'Projetei...') citando as tecnologias relevantes do repositório>
- **{labels['repo']}:** <URL do repositório no GitHub>

(Se houver repositórios no bloco 'PORTFÓLIO GITHUB', estruture os melhores projetos com suas URLs exatas. Caso nenhum repositório do GitHub seja fornecido, mantenha apenas projetos reais já descritos no currículo base sem inventar URLs.)

## {labels['education']}
### <Grau e curso>
*<Instituição> | <Ano de conclusão / previsão>*

## {labels['certifications']}
- **<Curso / certificação>:** <Instituição> (<Ano>)

## {labels['languages']}
<Idioma>: <Nível> | <Idioma>: <Nível>

REGRAS CRÍTICAS:
1. IDIOMA: todo o currículo DEVE estar em {labels['name']}. Se o currículo base estiver em outro idioma, TRADUZA integralmente.
2. BULLETS: sempre `- **Tópico:** ação`. Não use "●", "•" nem colchetes.
3. TABELA DE HABILIDADES: sempre a tabela Markdown de 2 colunas com a linha separadora `| :--- | :--- |`, listando de forma abrangente as tecnologias relevantes comprovadas no currículo base e no GitHub.
4. HONESTIDADE FACTUAL: NUNCA invente empresas, cargos, URLs ou tecnologias que não existam no currículo base ou nos repositórios do GitHub fornecidos.
5. VOZ EM 1ª PESSOA: Todos os bullets de experiência e projetos DEVEM ser redigidos em PRIMEIRA PESSOA ('Atuo...', 'Desenvolvi...', 'Implementei...').
6. Retorne APENAS o Markdown do currículo, sem comentários e sem cercas de código (```)."""


def build_general_resume_user_messages(
    system_prompt: str,
    base_resume: str,
    portfolio: str,
    extracted_techs_str: str,
    target_focus: str = "",
) -> list:
    """Monta as mensagens (System + Human) para o gerador de currículo geral."""
    focus_line = f"--- FOCO / TÍTULO DESEJADO ---\n{target_focus}\n\n" if target_focus.strip() else ""
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"--- CURRÍCULO BASE DO CANDIDATO ---\n{base_resume}"),
        HumanMessage(
            content=(
                f"{focus_line}"
                f"--- TECNOLOGIAS IDENTIFICADAS NO PERFIL E GITHUB (DESTACAR NO CURRÍCULO) ---\n{extracted_techs_str}\n\n"
                f"--- PORTFÓLIO GITHUB ---\n{portfolio}"
            )
        ),
    ]

