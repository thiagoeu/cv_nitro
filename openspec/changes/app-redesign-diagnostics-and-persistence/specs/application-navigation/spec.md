# Spec Delta: application-navigation

## Purpose

Fornece uma estrutura modular de navegação e menu para alternar entre visão executiva, assistente passo a passo de otimização, central de candidaturas e configurações da aplicação.

## ADDED Requirements

### Requirement: Navegação modular por menu
O sistema SHALL fornecer um menu de navegação que permita transitar entre as visões 'Dashboard', 'Nova Otimização', 'Central de Candidaturas' e 'Configurações'.

#### Scenario: Transição entre visões
- **WHEN** o usuário seleciona um item no menu de navegação
- **THEN** o sistema renderiza a tela correspondente preservando o estado global da sessão

### Requirement: Assistente de otimização em etapas
O sistema SHALL organizar o processo de entrada de dados e geração em seções bem delimitadas, incluindo upload de arquivo, dados da vaga e preferências de execução.

#### Scenario: Visualização do assistente
- **WHEN** o usuário acessa a seção de 'Nova Otimização'
- **THEN** os campos de entrada aparecem agrupados por etapas lógicas com indicadores visuais de progresso
