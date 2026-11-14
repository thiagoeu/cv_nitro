# Tasks: Invalidação e Atualização Sob Demanda do Cache do GitHub

## 1. Estado do Grafo e Agente GitHub Fetcher

- [x] 1.1 Adicionar o campo `force_github_refresh: Optional[bool] = False` ao `GraphState` em `src/agents/state.py` e verificar compatibilidade com tipagem existente.
- [x] 1.2 Modificar `github_fetcher` em `src/agents/nodes/github.py` para verificar `not state.get("force_github_refresh")` antes de retornar o cache e verificar comportamento via teste unitário mockado.
- [x] 1.3 Atualizar `src/core/profile_manager.py` para registrar o timestamp `github_synced_at` na execução de `update_cached_github_repos` e verificar persistência local e no Supabase.

## 2. Interface do Usuário e Sincronização Sob Demanda

- [x] 2.1 Implementar componente no formulário do Wizard (`src/ui/wizard_view.py`) exibindo a quantidade de repositórios cacheados, a data da última sincronização e o botão "Atualizar projetos agora" sem perder os campos preenchidos.
- [x] 2.2 Adicionar componente similar de exibição e sincronização de repositórios na geração de Currículo Geral em `src/ui/applications_view.py`.
- [x] 2.3 Criar helper de checagem leve `check_github_staleness` que compara a quantidade em cache com `public_repos` da API e exibe aviso informativo caso novos repositórios sejam detectados.

## 3. Testes Automatizados e Validação

- [x] 3.1 Escrever testes unitários em `tests/test_github_cache_invalidation.py` cobrindo o reaproveitamento de cache padrão, o disparo com `force_github_refresh` ativo e o registro de `github_synced_at`.
- [x] 3.2 Executar a suíte completa de testes com `pytest` sem chamadas de rede para assegurar conformidade e regressão zero.

