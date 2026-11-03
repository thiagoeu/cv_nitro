# Proposal: Mapeamento Semântico de Competências e Trava Factual Estrita

## Why

A validação atual de conformidade ATS utiliza comparações sintáticas literais por regex, o que penaliza injustamente o candidato ao rejeitar variações técnicas, versões e famílias tecnológicas correlatas (por exemplo, exigência de `HTML` não reconhecendo `HTML5`, `SQL` não reconhecendo `PostgreSQL` ou `MySQL`, e `Inteligência Artificial Generativa` não reconhecendo `IA Generativa` ou `RAG`). Essa rigidez rebaixa a pontuação do candidato mesmo quando ele domina a competência demandada.

Ao mesmo tempo, quando a vaga exige tecnologias que o candidato realmente não possui (por exemplo, vaga de C#/.NET para um perfil Node.js/React), o modelo de linguagem pode tentar "agradar" o ATS e alucinar atribuições nas experiências profissionais. É imperativo separar formalmente as competências comprovadas por equivalência daquelas que são pendências técnicas inegociáveis, garantindo notas justas sem jamais fabricar histórico profissional.

## What Changes

- **Agente/Etapa de Mapeamento de Competências (`competency_matcher`):** analisa os requisitos da vaga contra o currículo base e o portfólio do GitHub, classificando os requisitos em:
  - *Tecnologias Comprovadas e Equivalentes:* termos atendidos diretamente ou via versão/família tecnológica (`HTML5` $\rightarrow$ `HTML`, `PostgreSQL/MySQL` $\rightarrow$ `SQL`, `RESTful APIs` $\rightarrow$ `APIs REST`, `IA Generativa/LLMs` $\rightarrow$ `Inteligência Artificial Generativa`).
  - *Pendências Técnicas Reais (Gaps):* requisitos que não encontram respaldo no perfil do candidato (ex.: C#, .NET, Razor, Angular).
- **Fronteira Factual Rígida no `resume_generator`:** contrato explícito que proíbe o redator de inserir tecnologias da lista de pendências técnicas na tabela de habilidades ou nas experiências profissionais, destinando-as exclusivamente para o roteiro de entrevista e carta de apresentação.
- **Sourcing Estrito de Projetos:** instrução determinante para que a seção de projetos cite exclusivamente repositórios comprovados no portfólio, eliminando rejeições de URLs na primeira rodada.
- **Auditoria Reforçada no `quality_reviewer`:** verificação de conformidade que valida as equivalências técnicas e bloqueia versões que tentem inventar tecnologias marcadas como pendências técnicas.

## Capabilities

### Modified Capabilities

- `ats-optimization`: Enriquecimento do cálculo de compatibilidade ATS e diagnóstico para suportar correspondência semântica e equivalências tecnológicas reconhecidas de mercado, mantendo o isolamento claro das pendências técnicas.
- `resume-optimization`: Atualização do fluxo de geração e revisão de currículo com a camada de mapeamento de competências e imposição de fronteira factual estrita (whitelist de comprovadas e proibição de pendências no histórico).

## Impact

- `src/agents/state.py`: inclusão de `verified_technologies` e `unmatched_gaps` no estado compartilhado do grafo.
- `src/agents/nodes.py`: implementação da função `competency_matcher`, aprimoramento de `_term_in_text` com equivalências canônicas e diretrizes estritas no `resume_generator` e `quality_reviewer`.
- `src/agents/graph.py`: inserção do nó `competency_matcher` no fluxo do pipeline.
- `src/ui/diagnostic_view.py`: exibição visual de equivalências atendidas e pendências técnicas.
- Testes unitários em `tests/test_nodes.py`, `tests/test_agents.py` e `tests/test_state.py`.

