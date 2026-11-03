# Spec Delta

## MODIFIED Requirements

### Requirement: Gerar roteiro estratégico de preparação para entrevista
O sistema SHALL produzir orientações de preparação para entrevista técnica baseadas nas lacunas reais identificadas e nos projetos reais do candidato. Quando as orientações vierem do revisor por modelo, ele MUST ter recebido os requisitos da vaga e as pendências técnicas.

#### Scenario: Exibição de recomendações para entrevista com lacunas abertas
- **WHEN** o diagnóstico identifica lacunas técnicas ou projetos em destaque para a vaga
- **THEN** o painel apresenta tópicos de preparação indicando como defender as lacunas abertas e quais projetos do portfólio destacar ao recrutador

#### Scenario: Orientações do revisor por modelo em modo rígido
- **WHEN** a revisão roda em modo rígido e a vaga tem pendências técnicas
- **THEN** as orientações de entrevista geradas pelo revisor por modelo citam requisitos da vaga e as pendências técnicas, e não apenas o conteúdo do currículo
