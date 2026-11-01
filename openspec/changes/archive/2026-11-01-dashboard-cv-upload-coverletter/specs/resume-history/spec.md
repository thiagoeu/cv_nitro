# Spec Delta

## MODIFIED Requirements

### Requirement: Listar currículos gerados
O sistema SHALL exibir uma lista de todos os currículos salvos no histórico com metadados detalhados incluindo título da vaga, URL da vaga (quando disponível), data e status.

#### Scenario: Visualização do histórico vazio
- **WHEN** não há currículos salvos no armazenamento local
- **THEN** o sistema exibe uma mensagem indicando que o histórico está vazio

#### Scenario: Visualização do histórico com itens
- **WHEN** há currículos salvos
- **THEN** o sistema lista os currículos com título da vaga, data de criação e link direto para a vaga original

## ADDED Requirements

### Requirement: Armazenamento e recuperação de Cover Letter
O sistema SHALL persistir a Cover Letter gerada junto com o currículo no registro histórico e permitir a recuperação individual de ambos os documentos.

#### Scenario: Carregamento de aplicação com Cover Letter
- **WHEN** o usuário seleciona uma candidatura gravada no histórico
- **THEN** o sistema carrega tanto o currículo ajustado quanto a respectiva carta de apresentação
