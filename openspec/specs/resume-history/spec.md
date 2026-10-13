# resume-history Specification

## Purpose
Permite que o usuário acesse, visualize e gerencie todos os currículos otimizados gerados anteriormente.

## Requirements

### Requirement: Listar currículos gerados
O sistema SHALL exibir uma lista de todos os currículos salvos no histórico, ordenados pela data de geração.

#### Scenario: Visualização do histórico vazio
- **WHEN** não há currículos salvos no armazenamento local
- **THEN** o sistema exibe uma mensagem indicando que o histórico está vazio

#### Scenario: Visualização do histórico com itens
- **WHEN** há currículos salvos
- **THEN** o sistema lista os currículos com seus respectivos títulos da vaga e data

### Requirement: Carregar currículo salvo
O sistema SHALL carregar e exibir o conteúdo Markdown de um currículo ao ser selecionado no histórico.

#### Scenario: Seleção de currículo
- **WHEN** o usuário clica em um currículo específico na aba de histórico
- **THEN** o conteúdo completo do currículo é exibido na tela principal para cópia e leitura
