# Spec Delta

## ADDED Requirements

### Requirement: Mapear competências comprovadas e isolar pendências técnicas
O sistema SHALL classificar previamente os requisitos da vaga contra o perfil e portfólio do candidato em tecnologias comprovadas (diretas ou equivalentes) e pendências técnicas reais, proibindo estritamente a inserção de pendências técnicas na tabela de habilidades ou experiências profissionais do currículo gerado.

#### Scenario: Vaga com requisitos não comprovados pelo histórico
- **WHEN** a vaga exige tecnologias ausentes no currículo base e no portfólio do candidato (como C# ou .NET para perfil Node/React)
- **THEN** o sistema classifica esses termos estritamente como pendências técnicas e proíbe o gerador de atribuí-los às experiências profissionais ou à tabela de habilidades

#### Scenario: Uso exclusivo de repositórios comprovados em projetos
- **WHEN** a seção de projetos em destaque é redigida
- **THEN** o gerador utiliza exclusivamente os repositórios selecionados no portfólio comprovado do GitHub com suas respectivas URLs

