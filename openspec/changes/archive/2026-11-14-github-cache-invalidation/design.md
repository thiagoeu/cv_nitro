# Design: Invalidação e Atualização Sob Demanda do Cache do GitHub

## Contexto (Context)
Atualmente, o pipeline de agentes (`cv_nitro`) reaproveita `cached_repos` do perfil do usuário para economizar chamadas à API do GitHub e evitar custos de latência e tokens. No entanto, uma vez preenchido o cache, ele nunca expira automaticamente e o formulário de candidatura (`wizard_view.py`) não possui controle para atualização rápida. Veja mais detalhes motivacionais em `proposal.md`.

## Objetivos e Não-Objetivos (Goals / Non-Goals)

**Objetivos:**
- Permitir que o usuário visualize a contagem de repositórios em cache e acione a sincronização direta diretamente no formulário do Wizard e no fluxo de Currículo Geral, sem abandonar o preenchimento da vaga.
- Suportar a flag `force_github_refresh` no estado do LangGraph (`GraphState`), permitindo ao nó `github_fetcher` forçar a busca na API remota mesmo na presença de cache prévio.
- Armazenar o timestamp `github_synced_at` no perfil do usuário para auditoria e exibição de data da última sincronização na interface.
- Fornecer alerta visual de inconsistência quando a contagem de repositórios públicos no GitHub diferir da quantidade em cache.

**Não-Objetivos:**
- Criar rotinas automáticas de polling contínuo em segundo plano que consomem requisições desnecessárias da API do GitHub.
- Configurar webhooks do GitHub ou exigir autenticação OAuth avançada para repositórios privados (o escopo foca exclusivamente em repositórios públicos do candidato).

## Decisões Técnicas (Decisions)

### Decisão 1: Sincronização direta no formulário de candidatura com persistência de estado
- **Abordagem**: No `wizard_view.py` e em `general_workflow.py`, junto ao campo `github_username`, adicionar componente compacto informando a contagem de repositórios em cache e um botão de ação "Atualizar projetos agora".
- **Comportamento**: Ao clicar, o sistema invoca `github_fetcher`, atualiza o perfil via `profile_manager.update_cached_github_repos(uid, repos)` e atualiza o estado local da sessão sem resetar os textos já digitados para a vaga.
- **Alternativa descartada**: Realizar consulta remota a cada execução de pipeline. Descartada para proteger a cota da API (60 req/h sem token) e manter o tempo de resposta rápido.

### Decisão 2: Suporte a `force_github_refresh` no `GraphState` e no `github_fetcher`
- **Abordagem**: Adicionar o campo `force_github_refresh: Optional[bool]` no `GraphState`. No nó `github_fetcher`, a verificação de cache passa a ser:
  ```python
  if state.get("raw_github_repos") and not state.get("force_github_refresh"):
      # reaproveita cache
  ```
- **Racional**: Garante coerência arquitetural tanto para execuções interativas via Streamlit quanto para chamadas programáticas ou testes automatizados do grafo.

### Decisão 3: Registro de `github_synced_at` no Perfil
- **Abordagem**: Registrar data e hora ISO da última sincronização bem-sucedida em `profile["github_synced_at"]`.
- **Racional**: Fornece clareza temporal ao candidato (ex: "Sincronizado há 2 dias" ou data exata) facilitando saber se novos projetos já estão inclusos.

### Decisão 4: Checagem leve de contagem (`public_repos`)
- **Abordagem**: Implementar função auxiliar `check_github_staleness(username, cached_count)` que consulta `GET /users/{username}` (apenas 1 requisição leve de metadados). Se `public_repos != cached_count`, a interface exibe um aviso orientando a atualização.

## Riscos e Mitigações (Risks / Trade-offs)

- **[Risco]** Rate limit atingido na API pública do GitHub ao atualizar repositórios repetidamente.
  - **Mitigação**: Manter o uso do cache como comportamento padrão e seguro, acionando a API remota apenas sob clique intencional do usuário.
- **[Risco]** Perda do texto da vaga ao disparar o rerun do Streamlit no clique de sincronização.
  - **Mitigação**: Manter as chaves do `st.session_state` devidamente vinculadas aos inputs (`wizard_job_title`, `wizard_job_desc`, `wizard_base_resume`), garantindo retenção integral dos dados.

