# Spec Delta

## Purpose

Fornece transmissão contínua de eventos de status do fluxo de agentes e streaming em tempo real do texto gerado para a interface do usuário.

## ADDED Requirements

### Requirement: Emissão de eventos de progresso dos agentes
O sistema SHALL emitir eventos em tempo real indicando o início e a conclusão do processamento de cada nó do grafo multi-agente.

#### Scenario: Visualização do checklist de agentes em execução
- **WHEN** o usuário inicia a otimização de um currículo
- **THEN** a interface recebe notificações incrementais para cada agente concluído (análise de vaga, busca no GitHub, ranking e redação)

### Requirement: Streaming progressivo de texto do currículo
O sistema SHALL transmitir os blocos de texto gerados pelo gerador de currículo progressivamente para a interface antes da finalização completa do fluxo.

#### Scenario: Leitura de tokens em tempo real pelo usuário
- **WHEN** o nó gerador de currículo inicia a produção do documento Markdown
- **THEN** a interface exibe o texto gradualmente em um container dedicado sem bloqueio estático
