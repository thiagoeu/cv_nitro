# Spec Delta

## MODIFIED Requirements

### Requirement: Listar currículos gerados
O sistema SHALL exibir uma lista de todos os currículos salvos no histórico associados ao `user_id` do usuário conectado, ordenados da data mais recente à mais antiga.

#### Scenario: Visualização do histórico vazio
- **WHEN** não há currículos salvos para o usuário atual no histórico
- **THEN** o sistema exibe uma mensagem indicando que o histórico está vazio

#### Scenario: Visualização do histórico com itens
- **WHEN** há currículos salvos pertencentes ao usuário logado
- **THEN** o sistema lista os currículos com seus respectivos títulos da vaga, idioma, score ATS e data formatada
