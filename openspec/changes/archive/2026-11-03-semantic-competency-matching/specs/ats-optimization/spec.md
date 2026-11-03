# Spec Delta

## MODIFIED Requirements

### Requirement: Calcular pontuação de compatibilidade ATS auditável
O sistema SHALL calcular a pontuação de compatibilidade ATS (de 0 a 100) e o diagnóstico técnico com base na taxa efetiva de cobertura das tecnologias da vaga considerando correspondências semânticas e equivalências tecnológicas reconhecidas de mercado (versões, siglas e famílias como HTML5 para HTML, PostgreSQL/MySQL para SQL, IA Generativa para Inteligência Artificial Generativa e RESTful APIs para APIs REST), sem tolerar falsos positivos de tecnologias não relacionadas.

#### Scenario: Cálculo de pontuação baseado em evidências
- **WHEN** o currículo é avaliado pelo revisor
- **THEN** o sistema gera o score ATS combinando a proporção de tecnologias da vaga encontradas no texto (incluindo equivalências semânticas comprovadas) com a validação da tabela de habilidades e seções obrigatórias, sem gerar pontuações arbitrárias

#### Scenario: Diagnóstico detalhado de correspondência de termos
- **WHEN** a análise ATS é gerada
- **THEN** o diagnóstico lista explicitamente quais termos da vaga foram identificados (diretos ou equivalentes) e quais requisitos estruturais foram cumpridos

