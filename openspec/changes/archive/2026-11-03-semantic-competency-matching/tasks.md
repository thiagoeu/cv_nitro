# Tasks

## 1. Mapeador Semântico de Competências e Novo Nó no Grafo

- [x] 1.1 Criar `src/core/competency_matcher.py` contendo dicionário canônico de equivalências de mercado (`CANONICAL_EQUIVALENCES` para versões como `HTML5`/`HTML`, dialetos relacionais `PostgreSQL`/`MySQL`/`SQL`, siglas como `IA Generativa`/`Inteligência Artificial Generativa`, e padrões `RESTful`/`APIs REST`), função de correspondência semântica `matches_technology` e função `classify_competencies`, verificando com novos testes unitários em `tests/test_competency_matcher.py`.
- [x] 1.2 Atualizar `src/agents/state.py` adicionando `verified_technologies` e `unmatched_gaps` ao `AgentState`, implementar o nó `competency_matcher` em `src/agents/nodes.py` e integrá-lo ao fluxo do grafo em `src/agents/graph.py`, verificando com `pytest tests/test_state.py tests/test_agents.py`.

## 2. Fronteira Factual no Gerador e Auditoria ATS Justa

- [x] 2.1 Atualizar `resume_generator` em `src/agents/nodes.py` para receber o contrato de whitelist de `verified_technologies`, proibindo terminantemente a inclusão de tecnologias de `unmatched_gaps` nas experiências e habilidades e exigindo sourcing estrito dos projetos de `github_repos`, verificando com `pytest tests/test_nodes.py`.
- [x] 2.2 Integrar o matching por equivalências em `_validate_resume_deterministic` e `quality_reviewer` em `src/agents/nodes.py`, assegurando que o cálculo de score ATS reconheça termos equivalentes sem falso positivo e gere `missing_keywords` precisos para pendências reais, verificando com a suíte completa `pytest`.

