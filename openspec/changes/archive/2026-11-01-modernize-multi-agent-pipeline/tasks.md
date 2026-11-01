# Tasks

## 1. Estado e Paralelismo Inicial (Fan-out / Scatter-Gather)

- [x] 1.1 Atualizar `GraphState` em `src/agents/state.py` com campos de patch cirúrgico (`patch_section`, `patch_instruction`, `review_severity`) e verificar integridade de tipos com `pytest tests/test_state.py`
- [x] 1.2 Implementar nós `github_fetcher` e `relevance_ranker` desacoplados em `src/agents/nodes.py` e verificar ordenação determinística de repositórios com teste unitário
- [x] 1.3 Atualizar `build_graph()` em `src/agents/graph.py` para disparar `job_analyzer` e `github_fetcher` concorrentemente a partir do início e convergir em `relevance_ranker`
- [x] 1.4 Adicionar testes para a ramificação paralela inicial e validação de estado em `tests/test_agents.py` e verificar aprovação com `pytest tests/test_agents.py`

## 2. Tool-Calling sob Demanda e Otimização de Prefixos

- [x] 2.1 Implementar a tool `get_repo_deep_dive` para extração sob demanda de extratos técnicos de README e vincular ao nó `resume_generator` em `src/agents/nodes.py`
- [x] 2.2 Reorganizar a estrutura de mensagens do `resume_generator` com prefixos estáticos imutáveis (regras ATS e currículo base) para maximizar o reuso de Prompt Caching em GPU
- [x] 2.3 Implementar fallback defensivo que injeta metadados resumidos caso o modelo de contingência ativo não suporte chamada de ferramentas
- [x] 2.4 Criar testes unitários para o gerador de currículo com e sem acionamento de tools em `tests/test_nodes.py` e validar com `pytest tests/test_nodes.py`

## 3. Refinamento Cirúrgico de Seção (Delta Section Patching)

- [x] 3.1 Atualizar `quality_reviewer` em `src/agents/nodes.py` para retornar diagnóstico com severidade (`approved`, `minor`, `major`) e identificação da seção alvo
- [x] 3.2 Implementar a função utilitária de splice de seções Markdown e o nó `section_patcher` em `src/agents/nodes.py`
- [x] 3.3 Atualizar a lógica de roteamento `route_after_review` em `src/agents/graph.py` para encaminhar falhas `minor` ao `section_patcher` e falhas `major` ao gerador completo
- [x] 3.4 Criar testes de substituição cirúrgica de seções e tolerância a falhas de regex em `tests/test_agent_quality_improvements.py` e validar com `pytest tests/test_agent_quality_improvements.py`

## 4. Streaming em Tempo Real na Interface

- [x] 4.1 Atualizar `src/ui/wizard_view.py` para substituir a invocação bloqueante por iteração de streaming via `graph.stream(stream_mode="updates")`
- [x] 4.2 Integrar checklist dinâmico em `st.status` e renderização progressiva do currículo gerado via `st.empty()`
- [x] 4.3 Adicionar testes para o pipeline de streaming e tratamento de exceções em `tests/test_app_views.py` e validar com `pytest tests/test_app_views.py`

## 5. Validação Integrada do Sistema

- [x] 5.1 Executar a suíte completa de testes automatizados (`pytest`) e verificar que todos os testes (82+) passem com sucesso sem regressão
