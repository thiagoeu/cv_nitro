# Spec Delta: pipeline-streaming

## ADDED Requirements

### Requirement: Bloqueio de submissão concorrente durante geração
O sistema MUST desabilitar o botão principal de submissão do assistente de currículo (`wizard_submit_btn`) e impedir qualquer novo disparo concorrente enquanto a execução do pipeline multi-agente estiver em andamento.

#### Scenario: Botão desabilitado durante o processamento ativo
- **WHEN** o usuário aciona a geração do currículo otimizado no assistente
- **THEN** o botão de envio torna-se desabilitado para interação física e novos cliques são ignorados até a conclusão ou falha do fluxo

#### Scenario: Restauração do botão após conclusão ou erro
- **WHEN** a execução do pipeline multi-agente é concluída com sucesso ou interrompida por erro fatal
- **THEN** o botão de envio volta ao estado habilitado permitindo novas submissões

### Requirement: Alerta visual de retenção contra recarregamento da página
O sistema SHALL exibir um alerta visual proeminente na interface do assistente durante todo o período de processamento do grafo, orientando o usuário a não atualizar a página (F5) ou fechar a aba para evitar a perda do progresso.

#### Scenario: Exibição do aviso de retenção durante a execução
- **WHEN** o processamento do pipeline multi-agente é iniciado
- **THEN** a interface exibe um aviso em destaque orientando a permanência na tela enquanto os agentes trabalham

#### Scenario: Ocultação do aviso após término
- **WHEN** o processamento atinge o estado final e o currículo é persistido
- **THEN** o aviso temporário de retenção deixa de ser exibido e a tela transiciona para o resultado

