# Spec Delta

## MODIFIED Requirements

### Requirement: Calcular pontuação de compatibilidade ATS auditável
O sistema SHALL calcular a pontuação de compatibilidade ATS (de 0 a 100) e o diagnóstico técnico com base na taxa efetiva de cobertura das tecnologias da vaga considerando correspondências semânticas e equivalências tecnológicas reconhecidas de mercado (versões, siglas e famílias como HTML5 para HTML, PostgreSQL/MySQL para SQL, IA Generativa para Inteligência Artificial Generativa e RESTful APIs para APIs REST), sem tolerar falsos positivos de tecnologias não relacionadas. Uma família MUST valer só do item específico para o genérico, nunca entre itens irmãos, e a parcela da nota atribuída pelo revisor por modelo MUST considerar a vaga.

#### Scenario: Cálculo de pontuação baseado em evidências
- **WHEN** o currículo é avaliado pelo revisor
- **THEN** o sistema gera o score ATS combinando a proporção de tecnologias da vaga encontradas no texto (incluindo equivalências semânticas comprovadas) com a validação da tabela de habilidades e seções obrigatórias, sem gerar pontuações arbitrárias

#### Scenario: Diagnóstico detalhado de correspondência de termos
- **WHEN** a análise ATS é gerada
- **THEN** o diagnóstico lista explicitamente quais termos da vaga foram identificados (diretos ou equivalentes) e quais requisitos estruturais foram cumpridos

#### Scenario: Tecnologia irmã não conta como correspondência
- **WHEN** a vaga exige Jest e o currículo gerado cita apenas pytest
- **THEN** Jest não é contado como termo identificado e não aumenta a pontuação ATS

#### Scenario: Palavra comum não conta como tecnologia
- **WHEN** a vaga exige REST ou Go e o currículo gerado contém apenas "the rest of" ou "go-live"
- **THEN** o termo não é contado como identificado

#### Scenario: Nota do revisor por modelo considera a vaga
- **WHEN** a revisão roda em modo rígido e o revisor por modelo atribui sua nota
- **THEN** o revisor recebe o resumo da vaga, os termos ATS e as listas de tecnologias comprovadas e de pendências técnicas antes de pontuar
