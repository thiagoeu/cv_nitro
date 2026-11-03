# Tasks

## 1. Gerenciador de Cota e Contabilização de Tokens (`src/core/quota_manager.py`)

- [x] 1.1 Adicionar constantes configuráveis de orçamento diário (`GEMINI_DAILY_TOKEN_LIMIT`, `GEMINI_DAILY_REQUEST_LIMIT`, `GROQ_DAILY_TOKEN_LIMIT`, `GROQ_DAILY_REQUEST_LIMIT`) em `src/core/config.py` e criar `src/core/quota_manager.py` com funções de registro diário (`record_llm_usage`), extração/estimativa de tokens (`extract_or_estimate_tokens`), cálculo de porcentagem restante e estimativa de otimizações restantes (`get_quota_status`), reset de contadores (`reset_daily_quota`) e consulta de rate-limit do GitHub (`fetch_github_rate_limit`), verificando com novos testes unitários em `tests/test_quota_manager.py`.
- [x] 1.2 Instrumentar as chamadas de modelo em `src/agents/nodes.py` (`job_analyzer`, `resume_generator`, `section_patcher`, `quality_reviewer`, `cover_letter_generator`) para contabilizar automaticamente os tokens e requisições via `quota_manager.record_llm_usage`, verificando com `pytest tests/test_nodes.py tests/test_quota_manager.py`.

## 2. Barras Visuais de Porcentagem de Cota na Tela "Sistema" (`src/ui/settings_view.py`)

- [x] 2.1 Atualizar `render_settings_view` em `src/ui/settings_view.py` para renderizar o painel **"Monitor de Cota & Capacidade de Tokens"** com barras de progresso (`st.progress`) indicando a porcentagem restante (ex.: `90% disponível`), estimativa de otimizações restantes sem risco de erro `429`, barra de cota horária do GitHub e botões de atualização/reset, verificando com testes em `tests/test_app_views.py` e executando a suíte completa `pytest`.

