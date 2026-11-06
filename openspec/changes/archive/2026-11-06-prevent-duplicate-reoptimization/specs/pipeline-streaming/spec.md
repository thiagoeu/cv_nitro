# Spec Delta: pipeline-streaming

## MODIFIED Requirements

### Requirement: Bloqueio de submissão concorrente durante geração
O sistema MUST desabilitar os botões de submissão do assistente (`wizard_submit_btn`) e do painel de re-otimização (`btn_run_rerun_{filepath}` e `btn_toggle_rerun_{filepath}`) para impedir qualquer novo disparo concorrente enquanto a execução do pipeline multi-agente estiver em andamento.

#### Scenario: Botão desabilitado durante o processamento ativo
- **WHEN** o usuário aciona a geração do currículo otimizado no assistente
- **THEN** o botão de envio torna-se desabilitado para interação física e novos cliques são ignorados até a conclusão ou falha do fluxo

#### Scenario: Restauração do botão após conclusão ou erro
- **WHEN** a execução do pipeline multi-agente é concluída com sucesso ou interrompida por erro fatal
- **THEN** o botão de envio volta ao estado habilitado permitindo novas submissões

#### Scenario: Bloqueio no painel de re-otimização de candidaturas
- **WHEN** o usuário clica em executar a re-otimização de uma candidatura existente
- **THEN** os botões de execução e de fechar o painel tornam-se desabilitados até a conclusão ou falha do fluxo

### Requirement: Alerta visual de retenção contra recarregamento da página
O sistema SHALL exibir um alerta visual proeminente na interface do assistente ou do painel de re-otimização durante todo o período de processamento do grafo, orientando o usuário a não atualizar a página (F5) ou fechar a aba para evitar a perda do progresso.

#### Scenario: Exibição do aviso de retenção durante a execução
- **WHEN** o processamento do pipeline multi-agente é iniciado
- **THEN** a interface exibe um aviso em destaque orientando a permanência na tela enquanto os agentes trabalham

#### Scenario: Ocultação do aviso após término
- **WHEN** o processamento atinge o estado final e o currículo é persistido
- **THEN** o aviso temporário de retenção deixa de ser exibido e a tela transiciona para o resultado

#### Scenario: Exibição do aviso durante a re-otimização
- **WHEN** a re-otimização é disparada no painel de detalhes da candidatura
- **THEN** um aviso em destaque é renderizado acima do status alertando contra F5 e fechamento da aba

