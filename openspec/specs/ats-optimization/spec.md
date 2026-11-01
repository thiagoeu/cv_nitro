# ats-optimization Specification

## Purpose
Adiciona regras de otimização de ATS na geração de currículos para garantir leitura por sistemas automatizados.

## Requirements

### Requirement: Aplicar padrões ATS no currículo
O sistema SHALL estruturar o currículo gerado usando um layout padronizado de alta fidelidade com cabeçalho de contato, tabela de habilidades categorizada e itens de experiência orientados a impacto.

#### Scenario: Formatação com ATS
- **WHEN** o currículo é gerado
- **THEN** ele contém seções exatas como 'Resumo Profissional', 'Habilidades Técnicas', 'Experiência Profissional', 'Projetos em Destaque' e 'Formação Acadêmica' seguindo uma hierarquia visual limpa.

### Requirement: Estrutura padronizada de tópicos de experiência
O sistema SHALL formatar cada bullet point de experiência profissional seguindo o padrão de impacto com categoria em negrito seguida de verbo de ação e resultado mensurável.

#### Scenario: Geração de bullet de experiência
- **WHEN** uma experiência profissional é descrita
- **THEN** cada item inicia no formato '● **Tópico/Impacto:** Ação realizada e resultado', sem parágrafos genéricos soltos.

### Requirement: Tabela de habilidades técnicas categorizada
O sistema SHALL organizar as habilidades técnicas em categorias estruturadas com áreas de atuação claras e ferramentas correspondentes.

#### Scenario: Exibição de habilidades
- **WHEN** as habilidades técnicas são listadas no currículo
- **THEN** elas são apresentadas em categorias como 'Back-end & Arquitetura', 'Front-end & Mobile', 'Banco de Dados & ORM' e 'DevOps & Ferramentas'.

### Requirement: Apresentar diagnóstico detalhado de ATS
O sistema SHALL produzir e exibir um relatório de diagnóstico pós-otimização contendo score de aderência estimado, palavras-chave alinhadas, alterações efetuadas e parecer do revisor de qualidade.

#### Scenario: Exibição do painel de diagnóstico
- **WHEN** a otimização de um currículo é finalizada
- **THEN** o sistema apresenta uma seção de diagnóstico com as métricas de conformidade ATS e justificativas das modificações realizadas

### Requirement: Calcular pontuação de compatibilidade ATS auditável
O sistema SHALL calcular a pontuação de compatibilidade ATS (de 0 a 100) e o diagnóstico técnico com base na taxa efetiva de cobertura das tecnologias da vaga, presença de palavras-chave conceituais e conformidade dos blocos estruturais do currículo.

#### Scenario: Cálculo de pontuação baseado em evidências
- **WHEN** o currículo é avaliado pelo revisor
- **THEN** o sistema gera o score ATS combinando a proporção de tecnologias da vaga encontradas no texto com a validação da tabela de habilidades e seções obrigatórias, sem gerar pontuações arbitrárias

#### Scenario: Diagnóstico detalhado de correspondência de termos
- **WHEN** a análise ATS é gerada
- **THEN** o diagnóstico lista explicitamente quais termos da vaga foram identificados e quais requisitos estruturais foram cumpridos
