# Spec Delta

## Purpose

Otimiza currículos automaticamente cruzando vagas com repositórios do GitHub através de um fluxo de IA multi-agente.

## ADDED Requirements

### Requirement: Analisar descrição da vaga
O sistema SHALL extrair os requisitos, tecnologias e soft skills a partir de uma descrição de vaga fornecida pelo usuário.

#### Scenario: Vaga com requisitos claros
- **WHEN** uma vaga de "Desenvolvedor Python" é fornecida em texto
- **THEN** o sistema extrai "Python" e tecnologias relacionadas como requisitos

### Requirement: Buscar evidências no GitHub
O sistema SHALL consultar a API do GitHub do usuário para buscar repositórios e READMEs que demonstrem as habilidades exigidas pela vaga.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema seleciona o README deste repositório como evidência

### Requirement: Gerar currículo otimizado
O sistema SHALL gerar um currículo no formato Markdown incluindo uma seção de "Projetos em Destaque" baseada nas evidências extraídas do GitHub.

#### Scenario: Currículo gerado com sucesso
- **WHEN** os metadados do GitHub e os requisitos da vaga estão alinhados
- **THEN** um documento Markdown com o currículo ajustado é retornado

### Requirement: Revisar currículo gerado
O sistema SHALL revisar o currículo gerado contra alucinações, garantindo que não há informações ou repositórios inventados.

#### Scenario: Identificação de alucinação
- **WHEN** o currículo gerado cita uma ferramenta que não está no currículo original nem no GitHub
- **THEN** o revisor rejeita o currículo e solicita correção ao gerador
