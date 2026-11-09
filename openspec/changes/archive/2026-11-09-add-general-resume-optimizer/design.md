# Design

## Context

O fluxo atual (`src/agents/graph.py` e botão `wizard_submit_btn` em `src/ui/wizard_view.py`) foi projetado e calibrado especificamente para cruzar o currículo base com uma descrição de vaga (`job_analyzer` -> `relevance_ranker` -> `competency_matcher` -> `resume_generator` -> `quality_reviewer` -> `cover_letter_generator`). Conforme solicitado pelo usuário, esse fluxo principal já está exatamente como desejado e **não deve ser modificado**.

Para permitir que o usuário gere um **currículo geral de alto impacto** (sem precisar colar uma descrição de vaga, focando em estruturar um excelente currículo executivo citando todas as suas tecnologias relevantes e melhores projetos do GitHub), precisamos de um novo endpoint separado e de um segundo botão dedicado na tela do Otimizador (ver `proposal.md - Why`).

## Goals / Non-Goals

**Goals:**
- Criar um endpoint dedicado (`run_general_optimization` em `src/agents/general_workflow.py`) e prompts próprios (`src/agents/prompts/general_prompts.py`) que transformem o currículo base + portfólio GitHub em um currículo executivo A4 impecável, destacando as tecnologias relevantes do candidato.
- Reutilizar de forma somente-leitura peças utilitárias existentes (`github_fetcher`, `fetch_readmes_concurrently`, `LABELS`, `run_deterministic_checks`, `history_manager.save_resume`) sem alterar o comportamento do grafo principal.
- Adicionar um novo botão independente na tela do Otimizador (`src/ui/wizard_view.py`) que permita disparar esse endpoint geral exigindo apenas o currículo base.

**Non-Goals:**
- Alterar qualquer nó, aresta ou prompt do pipeline principal (`src/agents/graph.py`, `src/agents/nodes/analysis.py`, `src/agents/nodes/writer.py`, `src/agents/nodes/reviewer.py`).
- Exigir descrição de vaga no fluxo geral.

## Decisions

1. **Endpoint Separado (`src/agents/general_workflow.py`) em vez de Ramificações no `StateGraph` Principal**:
   - *Decisão*: Criar `src/agents/general_workflow.py` contendo a função de alto nível `run_general_optimization(base_resume, github_username, target_title, language, cached_repos, on_step)` e o gerador `generate_general_resume`.
   - *Racional*: Evita poluir `src/agents/graph.py` ou adicionar condicionais `"if not job_description"` dentro de `job_analyzer`, `competency_matcher` e `resume_generator`. O primeiro fluxo permanece 100% intocado, enquanto o novo endpoint tem um ciclo enxuto e rápido:
     1. **Coleta e Seleção de Portfólio Geral**: Reutiliza `github_fetcher` (ou `cached_repos` do perfil) para obter repositórios públicos não-fork, pontua-os por relevância geral (presença de linguagem/tópicos/descrição, estrelas e interseção com termos do currículo base) e baixa concorrentemente os READMEs higienizados dos Top 3 projetos via `fetch_readmes_concurrently`.
     2. **Redação Executiva Geral + Extração de Tecnologias Relevantes**: Invoca o LLM com `GENERAL_RESUME_SYSTEM_PROMPT` (`src/agents/prompts/general_prompts.py`), que estrutura o currículo no layout A4 canônico (`# Nome`, `## RESUMO PROFISSIONAL`, `## HABILIDADES TÉCNICAS` em tabela categorizada com todas as tecnologias relevantes do perfil/GitHub, `## EXPERIÊNCIA PROFISSIONAL` em 1ª pessoa ativa, `## PROJETOS EM DESTAQUE`, `## FORMAÇÃO ACADÊMICA`, `## IDIOMAS`).
     3. **Validação Determinística e Diagnóstico de Perfil Geral**: Executa `run_deterministic_checks` para garantir integridade estrutural (sem placeholders ou URLs inventadas) e monta o dicionário `diagnostic` (pontuação de completude/impacto ATS, lista de tecnologias relevantes destacadas em `matched_keywords`, pontos fortes do perfil e sugestões de melhoria), permitindo salvar via `history_manager.save_resume` e abrir diretamente na tela de **Candidaturas**.

2. **Segundo Botão Dedicado em `src/ui/wizard_view.py` + Suporte Completo a Edição e Adição de Projetos**:
   - *Decisão*: Na parte inferior de `render_wizard_view`, manter o botão primário original (`"Gerar currículo otimizado e diagnóstico ATS"`, key `"wizard_submit_btn"`) intacto e adicionar logo abaixo uma seção dedicada ao **Currículo Geral (Sem Vaga Específica)** contendo:
     - Seletor compacto de idioma (`pt`, `en`, `es`).
     - Campo opcional de **Links de projetos específicos do GitHub** (caso o usuário já queira forçar a inclusão de determinados repositórios na geração inicial).
     - Botão **"✨ Gerar currículo geral de alto impacto (sem vaga específica)"** (`key="wizard_general_submit_btn"`).
   - Além disso, na tela do currículo gerado (`src/ui/applications_view.py` / `src/ui/application_tabs.py`), adicionar um botão de acesso rápido no cabeçalho (**"Editar / Adicionar Projetos"**) e garantir que a seção **"Incrementar Projetos em Destaque por Link (GitHub + IA)"** e o editor funcionem perfeitamente para currículos gerais (mesmo sem descrição de vaga associada).

## Risks / Trade-offs

- **[Risk] Concorrência de cliques entre os dois botões na tela do Otimizador** → *Mitigation*: Ambos os botões respeitam a trava `st.session_state.wizard_is_generating`, ficando desabilitados enquanto qualquer uma das duas otimizações estiver em andamento.
- **[Risk] Idioma do currículo geral quando não há descrição de vaga** → *Mitigation*: Oferecer seletor de idioma padrão (`Português`, `Inglês`, `Espanhol`) para o modo geral (padrão `pt`), garantindo que os cabeçalhos canônicos (`LABELS[lang]`) saiam no idioma escolhido.

