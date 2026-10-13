# Design: ats-and-refactor

## Architecture
- Refatoração puramente estrutural em pastas. O orquestrador continua no LangGraph e a interface no Streamlit.
- O prompt do `resume_generator` será estendido para atuar como um otimizador ATS.

## Key Changes
- `config.py` e `history_manager.py` vão para `src/core/`.
- `graph.py`, `state.py` e `nodes.py` vão para `src/agents/`.
- `app.py` continua na raiz com importações atualizadas.
- Modificação no `system_prompt` do nó gerador exigindo regras de ATS.
