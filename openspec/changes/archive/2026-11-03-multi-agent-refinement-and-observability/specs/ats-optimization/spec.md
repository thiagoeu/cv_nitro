# Spec Delta

## MODIFIED Requirements

### Requirement: Apresentar diagnóstico detalhado de ATS
O sistema SHALL produzir e exibir um relatório de diagnóstico pós-otimização contendo score de aderência estimado, palavras-chave alinhadas, lacunas identificadas, repositórios do GitHub selecionados, orientações para entrevista, rastro de execução dos agentes, alterações efetuadas e parecer do revisor de qualidade.

#### Scenario: Exibição do painel de diagnóstico
- **WHEN** a otimização de um currículo é finalizada
- **THEN** o sistema apresenta uma seção de diagnóstico com as métricas de conformidade ATS e justificativas das modificações realizadas

#### Scenario: Exibição de lacunas, portfólio curado e trilha de agentes
- **WHEN** o painel de diagnóstico ATS é renderizado com dados de lacunas, projetos ranqueados e rastro de execução
- **THEN** a interface exibe os badges de requisitos ausentes, os repositórios escolhidos com seus scores de relevância, as recomendações de entrevista e a linha do tempo de deliberação dos agentes

