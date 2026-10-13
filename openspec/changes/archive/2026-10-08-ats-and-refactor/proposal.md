# Proposal: ats-and-refactor

## Problem / Opportunity
A estrutura inicial do projeto colocava todos os arquivos na raiz, dificultando a manutenção futura. Além disso, o currículo gerado necessitava de formatações específicas voltadas a algoritmos de ATS (Applicant Tracking Systems) para aumentar a taxa de aprovação dos candidatos em vagas reais, indo além da simples inclusão de projetos do GitHub.

## Proposed Solution
- Refatorar a estrutura do projeto movendo as lógicas para dentro da pasta `src/` modularizada (`core/` e `agents/`) e movendo testes para a pasta `tests/`.
- Ajustar as importações no `app.py` e testes.
- Atualizar o prompt do `resume_generator` em `src/agents/nodes.py` impondo regras estritas de otimização de ATS, como seções padronizadas, extração literal de palavras-chave da vaga, e reescrita de bullet points com verbos de ação e foco em impacto, além de impedir alucinações.

## Scope
- Diretórios:
  - `src/core/` para arquivos utilitários e configurações.
  - `src/agents/` para lógica do LangGraph.
  - `tests/` para todos os scripts de teste.
- Atualização exclusiva do agente gerador (prompt) no arquivo `nodes.py`.

## Capabilities
- ats-optimization: Otimização de ATS no gerador de currículos.
