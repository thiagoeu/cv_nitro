# agent-execution-observability Specification

## Purpose

Fornece rastreabilidade e observabilidade detalhada da execução e deliberação do grafo multi-agente, registrando cada etapa, decisão de roteamento e métrica intermediária para exibição ao usuário.

## Requirements

### Requirement: Registrar rastro estruturado de execução dos agentes
O sistema SHALL acumular no estado compartilhado do grafo um registro cronológico de eventos (`agent_trace`) contendo o identificador do agente, resumo da decisão ou artefato produzido e metadados da etapa.

#### Scenario: Execução de agentes concorrentes e sequenciais
- **WHEN** o pipeline multi-agente executa os nós de análise de vaga, busca no GitHub, ranqueamento, redação e revisão
- **THEN** cada nó registra sua entrada correspondente na trilha de auditoria sem sobrescrever os eventos emitidos por nós paralelos

#### Scenario: Registro de iteração de revisão e reparo cirúrgico
- **WHEN** o revisor de qualidade rejeita uma versão preliminar e aciona o refinamento de seção ou regeneração
- **THEN** a trilha de execução registra o motivo da reprovação, a severidade classificada, a seção afetada e a pontuação obtida na tentativa

### Requirement: Persistir e exibir linha do tempo de deliberação dos agentes
O sistema SHALL persistir o rastro de execução dos agentes junto ao diagnóstico da candidatura e apresentá-lo visualmente no painel de diagnóstico.

#### Scenario: Consulta ao histórico de deliberação na interface
- **WHEN** o usuário abre a aba de Diagnóstico ATS de uma candidatura recém-gerada ou carregada do histórico
- **THEN** a interface exibe a sequência de agentes acionados, as decisões tomadas em cada etapa e se houve restauração de snapshot ou reparo cirúrgico
