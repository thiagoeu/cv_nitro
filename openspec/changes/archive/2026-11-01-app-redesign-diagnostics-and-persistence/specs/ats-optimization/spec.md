# Spec Delta: ats-optimization

## ADDED Requirements

### Requirement: Apresentar diagnóstico detalhado de ATS
O sistema SHALL produzir e exibir um relatório de diagnóstico pós-otimização contendo score de aderência estimado, palavras-chave alinhadas, alterações efetuadas e parecer do revisor de qualidade.

#### Scenario: Exibição do painel de diagnóstico
- **WHEN** a otimização de um currículo é finalizada
- **THEN** o sistema apresenta uma seção de diagnóstico com as métricas de conformidade ATS e justificativas das modificações realizadas
