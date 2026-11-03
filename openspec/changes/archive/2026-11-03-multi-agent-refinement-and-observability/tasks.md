# Tasks

## 1. Estado Compartilhado e Rastreabilidade de Agentes (`GraphState` e Concorrência)

- [x] 1.1 Estender `GraphState` em `src/agents/state.py` e `build_initial_state` em `src/ui/wizard_view.py` com `agent_trace: Annotated[List[Dict[str, Any]], operator.add]` e campos de snapshot (`best_resume_md`, `best_ats_score`, `best_diagnostic`, `stop_reason`), verificando com `pytest tests/test_state.py` que a tipagem e inicialização passam.
- [x] 1.2 Paralelizar o download dos Top 3 READMEs em `relevance_ranker` (`src/agents/nodes.py`) utilizando `concurrent.futures.ThreadPoolExecutor` e emitir entradas de `agent_trace` em `job_analyzer`, `github_fetcher`, `relevance_ranker`, `resume_generator`, `section_patcher` e `cover_letter_generator`, verificando com `pytest tests/test_nodes.py`.

## 2. Snapshot & Rollback da Melhor Versão, Análise de Lacunas e Guia de Entrevista

- [x] 2.1 Atualizar `_validate_resume_deterministic` e `quality_reviewer` em `src/agents/nodes.py` para calcular `missing_keywords` (lacunas reais da vaga), anexar `curated_repos` (com score de relevância) e gerar `interview_tips` (híbrido via `ReviewResult` e determinístico), verificando com testes unitários em `tests/test_nodes.py`.
- [x] 2.2 Implementar a lógica de *Snapshot & Rollback* e parada por estagnação (`no_improvement`) em `quality_reviewer` (`src/agents/nodes.py`) e `route_after_review` (`src/agents/graph.py`), garantindo que revisões sem ganho de score restaurem a melhor versão válida e encerrem o loop, verificando com novos testes em `tests/test_agents.py`.

## 3. Painel de Diagnóstico ATS Enriquecido (Observabilidade, Gaps e Entrevista na UI)

- [x] 3.1 Persistir `agent_trace`, `missing_keywords`, `curated_repos`, `interview_tips` e `stop_reason` dentro do dicionário `diagnostic` em `save_pipeline_result` (`src/ui/wizard_view.py`) e atualizar `render_ats_diagnostic_panel` (`src/ui/diagnostic_view.py`) para exibir os badges de Lacunas Identificadas (*Gaps*), os Repositórios Curados do GitHub com score, o Guia de Preparação para Entrevista e a Linha do Tempo de Deliberação dos Agentes (`agent_trace`), verificando com testes em `tests/test_ui.py`.
- [x] 3.2 Atualizar a documentação da arquitetura multi-agente no `README.md` descrevendo o mecanismo de *Snapshot & Rollback*, a análise de lacunas e a telemetria `agent_trace`, e executar a suíte completa `pytest` garantindo 100% dos testes passando sem acesso à rede.

