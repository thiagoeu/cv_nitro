# Spec Delta: resume-optimization

## ADDED Requirements

### Requirement: Controle modular de etapas e economia de tokens
O sistema SHALL permitir a execução configurável do pipeline multi-agente, possibilitando ativar ou desativar etapas opcionais para redução no consumo de tokens e tempo de resposta.

#### Scenario: Execução em modo econômico sem carta de apresentação
- **WHEN** o usuário desmarca a geração de Cover Letter nas opções da otimização
- **THEN** o pipeline ignora o nó de geração de carta e consome tokens apenas para o currículo e diagnóstico

#### Scenario: Execução com revisão simplificada
- **WHEN** o usuário ativa o modo econômico de tokens
- **THEN** o sistema executa prompts enxutos de resumo de contexto e limita loops de refinamento da LLM
