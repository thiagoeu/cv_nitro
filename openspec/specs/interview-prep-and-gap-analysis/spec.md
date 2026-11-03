# interview-prep-and-gap-analysis Specification

## Purpose

Identifica de forma transparente as lacunas técnicas e conceituais entre a vaga e o perfil do candidato, expõe a curadoria de repositórios do GitHub e gera orientações de preparação para entrevista.

## Requirements

### Requirement: Identificar lacunas reais de requisitos da vaga
O sistema SHALL identificar e listar explicitamente as tecnologias e palavras-chave exigidas pela vaga que não foram encontradas no currículo gerado (`missing_keywords`), preservando a fidelidade factual sem inventar experiências.

#### Scenario: Vaga com tecnologias ausentes na base do candidato
- **WHEN** a descrição da vaga exige uma tecnologia que o candidato não possui no currículo base nem no portfólio do GitHub
- **THEN** o sistema não insere a tecnologia de forma fabricada no currículo e a registra na lista de lacunas identificadas do diagnóstico

### Requirement: Expor curadoria e pontuação de repositórios do GitHub
O sistema SHALL registrar no diagnóstico os repositórios selecionados pelo agente de ranqueamento com suas respectivas pontuações de relevância e linguagem principal.

#### Scenario: Candidatura com projetos selecionados do GitHub
- **WHEN** o agente de ranqueamento seleciona os repositórios mais aderentes à vaga
- **THEN** o diagnóstico armazena e exibe os projetos escolhidos juntamente com o score de relevância calculado para cada um

### Requirement: Gerar roteiro estratégico de preparação para entrevista
O sistema SHALL produzir orientações de preparação para entrevista técnica baseadas nas lacunas reais identificadas e nos projetos reais do candidato.

#### Scenario: Exibição de recomendações para entrevista com lacunas abertas
- **WHEN** o diagnóstico identifica lacunas técnicas ou projetos em destaque para a vaga
- **THEN** o painel apresenta tópicos de preparação indicando como defender as lacunas abertas e quais projetos do portfólio destacar ao recrutador
