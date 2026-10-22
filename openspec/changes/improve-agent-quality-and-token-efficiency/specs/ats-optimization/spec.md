# Spec Delta: ats-optimization

## ADDED Requirements

### Requirement: Calcular pontuação de compatibilidade ATS auditável
O sistema SHALL calcular a pontuação de compatibilidade ATS (de 0 a 100) e o diagnóstico técnico com base na taxa efetiva de cobertura das tecnologias da vaga, presença de palavras-chave conceituais e conformidade dos blocos estruturais do currículo.

#### Scenario: Cálculo de pontuação baseado em evidências
- **WHEN** o currículo é avaliado pelo revisor
- **THEN** o sistema gera o score ATS combinando a proporção de tecnologias da vaga encontradas no texto com a validação da tabela de habilidades e seções obrigatórias, sem gerar pontuações arbitrárias

#### Scenario: Diagnóstico detalhado de correspondência de termos
- **WHEN** a análise ATS é gerada
- **THEN** o diagnóstico lista explicitamente quais termos da vaga foram identificados e quais requisitos estruturais foram cumpridos
