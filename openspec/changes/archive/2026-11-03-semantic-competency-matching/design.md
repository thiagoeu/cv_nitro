# Design: Mapeamento Semântico de Competências e Trava Factual Estrita

## Context

Atualmente, a avaliação de compatibilidade ATS em `src/agents/nodes.py` depende de `_term_in_text`, que utiliza uma expressão regular estrita `(?<![a-zA-Z0-9]){re.escape(term_clean)}(?![a-zA-Z0-9])`. Isso gera falsos negativos graves:
- `HTML` não dá match com `HTML5` devido ao dígito numérico após o radical.
- `SQL` não reconhece dialetos relacionais explícitos como `PostgreSQL` ou `MySQL`.
- `Inteligência Artificial Generativa` não dá match com `IA Generativa` ou `RAG`.
- `APIs REST` não dá match com `RESTful APIs`.

Além disso, o `resume_generator` não recebe uma delimitação formal entre o que o candidato realmente comprovou no currículo/portfólio e o que é pendência técnica da vaga. Sem essa fronteira, a LLM pode tentar inserir tecnologias da vaga no histórico do candidato, ou gerar links de repositórios que não existem na listagem pública do GitHub.

## Goals / Non-Goals

**Goals:**
- Implementar tabela canônica de equivalências técnicas e semânticas de mercado em `src/core/competency_matcher.py` cobrindo variantes de versões (`HTML5` $\leftrightarrow$ `HTML`, `ES6` $\leftrightarrow$ `JavaScript`), siglas/extenso (`IA Generativa` $\leftrightarrow$ `Inteligência Artificial Generativa`), dialetos e famílias (`PostgreSQL`, `MySQL`, `SQLite` $\leftrightarrow$ `SQL`; `REST`, `RESTful` $\leftrightarrow$ `APIs REST`).
- Implementar o nó/etapa `competency_matcher` no grafo, dividindo os requisitos da vaga em `verified_technologies` (comprovadas por histórico ou equivalência) e `unmatched_gaps` (pendências técnicas reais).
- Injetar no `resume_generator` um contrato de whitelist estrito: apenas `verified_technologies` e repositórios de `github_repos` podem entrar no currículo; `unmatched_gaps` são terminantemente proibidas de serem atribuídas ao histórico profissional.
- Atualizar a validação determinística do `quality_reviewer` para pontuar equivalências de forma justa e rejeitar alucinações de pendências técnicas.

**Non-Goals:**
- Não criar equivalências falsas entre linguagens e frameworks distintos (ex.: `Node.js` nunca equivalerá a `C#` ou `Python`; `React` nunca equivalerá a `Angular`).
- Não aumentar o custo ou tempo de execução com chamadas recursivas adicionais de LLM: a resolução de equivalências é projetada para ser híbrida, ultra-rápida (tempo < 5ms) e determinística.

## Decisions

### Decisão 1: Mapeador Canônico de Equivalências Tecnológicas (`src/core/competency_matcher.py`)
- **Escolha:** Estruturar um módulo dedicado com grupos de equivalência canônica (sinônimos, versões e termos guarda-chuva) com normalização fonética e de símbolos (`c#`, `c++`, `.net`, `node.js`).
- **Alternativa Considerada:** Usar embeddings semânticos vetoriais pesados. Rejeitada porque embeddings introduzem falsos positivos (ex.: considerar `React` similar a `Angular` por proximidade vetorial em frontend, quando são tecnologias distintas).

### Decisão 2: Fronteira de Estado `verified_technologies` vs `unmatched_gaps`
- **Escolha:** O estado compartilhado passa a carregar explicitamente quais tecnologias da vaga foram comprovadas no currículo/GitHub e quais permaneceram como pendência técnica.
- **Benefício:** Dá clareza total na UI (badges de termos alinhados vs pendências técnicas) e fornece um contrato inequívoco para os prompts do gerador e do revisor.

### Decisão 3: Contrato de Whitelist no Prompt do `resume_generator`
- **Escolha:** Prompt com proibição explícita e sancionada:
  - Tecnologias em `unmatched_gaps` não podem figurar nas experiências nem na tabela de habilidades.
  - Projetos em destaque devem usar exclusivamente as URLs e nomes de `github_repos`.
- **Benefício:** Elimina retrabalho de `section_patcher` por links inexistentes e previne a fabricação indevida de histórico técnico.

## Risks / Trade-offs

- **[Risco] Falsos positivos por generalização excessiva:**  
  *Mitigação:* As regras de equivalência agrupam apenas variações diretas (versões, siglas, dialetos de banco comprovados). Nenhuma equivalência cruzará linguagens de programação diferentes (ex.: Java $\neq$ C#) ou frameworks principais concorrentes (ex.: Vue $\neq$ React).
- **[Risco] Repositórios válidos declarados no currículo base não presentes na API do GitHub:**  
  *Mitigação:* O `competency_matcher` aceita repositórios comprovados no `base_resume` desde que não haja conflito com a lista da API, ou prioriza a lista curada pelo `relevance_ranker`.

