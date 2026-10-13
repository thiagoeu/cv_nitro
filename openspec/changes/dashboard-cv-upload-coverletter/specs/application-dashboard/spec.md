# Spec Delta

## Purpose

Fornece um painel visual consolidado na página inicial com métricas de candidaturas, gráficos de tecnologias aplicadas e tabela interativa com links das vagas e datas de ajuste.

## ADDED Requirements

### Requirement: Exibir métricas e gráficos das candidaturas
O sistema SHALL exibir no topo da página inicial indicadores-chave (total de vagas aplicadas, tecnologias mais frequentes) e visualizações gráficas das candidaturas salvas.

#### Scenario: Visualização do dashboard com dados existentes
- **WHEN** o usuário acessa a página inicial e existem candidaturas salvas no histórico
- **THEN** o sistema renderiza cartões com métricas e gráfico sumarizando as tecnologias e distribuição de vagas

#### Scenario: Visualização do dashboard sem dados
- **WHEN** não há nenhuma candidatura no histórico
- **THEN** o sistema exibe uma mensagem informativa incentivando a primeira otimização de currículo

### Requirement: Tabela consolidada de histórico de vagas
O sistema SHALL exibir uma tabela interativa listando as vagas otimizadas com título da vaga, link de acesso à vaga (quando informado), data de geração e atalhos para visualização rápida.

#### Scenario: Listagem de vagas com links clicáveis
- **WHEN** a tabela de aplicações é exibida
- **THEN** cada linha mostra a vaga, a data/hora do ajuste e um link funcional para o anúncio da vaga (ou indicador visual se não houver link)

#### Scenario: Acesso rápido aos artefatos gerados
- **WHEN** o usuário clica para visualizar uma aplicação da tabela
- **THEN** o sistema abre a visualização detalhada contendo o currículo otimizado e a carta de apresentação gerada
