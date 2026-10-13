# Spec Delta

## MODIFIED Requirements

### Requirement: Aplicar padrões ATS no currículo
O sistema SHALL estruturar o currículo gerado usando um layout padronizado de alta fidelidade com cabeçalho de contato, tabela de habilidades categorizada e itens de experiência orientados a impacto.

#### Scenario: Formatação com ATS
- **WHEN** o currículo é gerado
- **THEN** ele contém seções exatas como 'Resumo Profissional', 'Habilidades Técnicas', 'Experiência Profissional', 'Projetos em Destaque' e 'Formação Acadêmica' seguindo uma hierarquia visual limpa.

## ADDED Requirements

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
