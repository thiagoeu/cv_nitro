# Proposal

## Why

Durante o uso do sistema (especialmente em demonstrações acadêmicas ou rodadas consecutivas de otimização), o usuário não tem visibilidade de quantos tokens e requisições já consumiu nos provedores de IA (Gemini e Groq) nem de quanto resta de cota na API do GitHub. Isso gera incerteza sobre se as próximas otimizações irão rodar normalmente ou esbarrar em erros de limite de taxa (`HTTP 429`).

## What Changes

- **Rastreador de Consumo e Cota de Tokens (`quota_manager.py`)**: Novo módulo em `src/core/quota_manager.py` que contabiliza tokens de entrada/saída e número de requisições por provedor (`gemini`, `groq`) a cada execução de nó do grafo, persistindo o consumo diário e por minuto com orçamento diário configurável (padrão compatível com o Free Tier do Gemini e Groq).
- **Consulta ao Vivo de Limites da API do GitHub e Sonda de Saúde dos Modelos**: Função para consultar em tempo real a cota restante da API do GitHub (`GET /rate_limit`, exibindo ex.: `92% restante — 55/60 req/h`) e botão opcional de verificação rápida de disponibilidade dos provedores de IA.
- **Barras Visuais de Cota Restante na Tela "Sistema" (`settings_view.py`)**: Adição do painel **"📊 Monitor de Cota & Capacidade de Tokens"** na página de configurações (`Sistema`), exibindo barras de progresso (`st.progress`) com a porcentagem restante (ex.: `90% disponível` em verde, alerta em amarelo abaixo de `25%` e crítico em vermelho abaixo de `10%`), estimativa de quantas otimizações completas ainda cabem na cota do dia e botão para zerar/atualizar o medidor.

## Capabilities

### New Capabilities
- `quota-and-token-monitoring`: Contabilização de tokens e requisições consumidos pelos agentes de IA, consulta de rate-limit da API do GitHub e exibição visual em barras de progresso de cota restante com estimativa de capacidade operacional na tela de Sistema.

### Modified Capabilities
<!-- Nenhuma capability existente tem seus requisitos normativos alterados -->

## Impact

- **Núcleo (`src/core/`)**: Novo módulo `src/core/quota_manager.py` e variáveis opcionais de limite diário em `src/core/config.py`.
- **Agentes (`src/agents/`)**: Instrumentação leve em `src/agents/nodes.py` para registrar tokens/chamadas consumidos nas invocações de LLM.
- **Interface (`src/ui/`)**: Expansão de `src/ui/settings_view.py` com as barras de porcentagem de cota restante (`90%`, `10%`, etc.), indicadores de saúde para as próximas execuções e consulta de rate-limit do GitHub.
- **Testes (`tests/`)**: Novos testes unitários em `tests/test_quota_manager.py` e `tests/test_app_views.py`.

