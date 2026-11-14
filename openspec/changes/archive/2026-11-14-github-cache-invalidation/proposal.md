# Proposta: Invalidação e Atualização Sob Demanda do Cache do GitHub

## Por que (Why)
Atualmente, o sistema armazena os repositórios públicos do GitHub em cache no perfil do usuário (`cached_repos`) para economizar chamadas de API e acelerar a execução do pipeline de agentes. No entanto, esse cache é estático e permanente: quando o usuário cria novos repositórios, altera projetos ou ajusta tópicos no GitHub, o agente `github_fetcher` continua reaproveitando a lista antiga gravada no cache do perfil sem detectar a defasagem.

Para que novos projetos ou alterações recentes entrem no radar das otimizações de currículo, o usuário é obrigado a navegar manualmente até a tela de Perfil e acionar o botão de sincronização antes de iniciar uma nova candidatura. Se o usuário não fizer isso conscientemente, repositórios recém-criados de alto valor técnico para a vaga são completamente ignorados pelos agentes de curadoria e redação.

## O que muda (What Changes)
- **Controle de sincronização direta no Wizard de Otimização e no Fluxo Geral**: inclusão de indicador de repositórios em cache (quantidade e status) com botão rápido para sincronizar/atualizar os projetos do GitHub no próprio formulário da candidatura.
- **Detecção de defasagem (Cache Staleness Check)**: mecanismo de verificação leve da contagem de repositórios públicos via metadados do usuário no GitHub (`public_repos`) ou parâmetro de força de atualização (`force_refresh`), alertando o usuário ou renovando o cache automaticamente quando a contagem diferir do total em cache.
- **Suporte a parâmetro de atualização forçada no pipeline multi-agente**: permissão para que o estado inicial (`GraphState`) receba uma flag de atualização forçada que instrui o `github_fetcher` a consultar a API remota mesmo se `cached_repos` estiver preenchido, regravando o perfil atualizado.

## Capacidades (Capabilities)

### Capacidades Novas (New Capabilities)
Nenhuma nova capacidade durable é criada; a evolução estende a persistência e o reuso de perfil já existentes.

### Capacidades Modificadas (Modified Capabilities)
- `user-profile-reuse`: expandir o requisito de cache de repositórios para incluir detecção de defasagem de repositórios, suporte a invalidação/atualização forçada e sincronização sob demanda no fluxo de geração de currículo.

## Impacto (Impact)
- **Interface (UI)**: `src/ui/wizard_view.py` e `src/ui/applications_view.py` (fluxo de currículo geral) passam a exibir status do cache e botão de atualização rápida de repositórios.
- **Nós de Agentes e Estado**: `src/agents/state.py` recebe campo opcional `force_github_refresh: bool`; `src/agents/nodes/github.py` valida essa instrução antes do reaproveitamento do cache.
- **Gerenciador de Perfil**: `src/core/profile_manager.py` ganha registro de data/hora da última sincronização (`github_synced_at`) para facilitar rastreamento e auditoria de frescor dos dados.
- **Dependências e APIs**: Nenhuma nova dependência externa; uso otimizado do endpoint público da API do GitHub respeitando limites de requisição.

