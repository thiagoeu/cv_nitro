# Spec Delta

## Purpose

Estabelece a divisão modular da interface em componentes de responsabilidade única no diretório src/ui, desacoplando roteamento, autenticação, formulários e visualizações analíticas.

## ADDED Requirements

### Requirement: Desacoplamento da camada de apresentação
O sistema SHALL estruturar cada seção visual em módulos especializados dentro de `src/ui/`, mantendo `app.py` exclusivamente como roteador e inicializador de ciclo de vida.

#### Scenario: Renderização modularizada de rotas
- **WHEN** uma rota específica da aplicação é acionada
- **THEN** o arquivo `app.py` delega a renderização para a respectiva view especializada em `src/ui/` sem conter lógica acoplada de formulários ou formatação complexa

### Requirement: Isolamento de estados de visualização
O sistema SHALL manter o estado de cada view isolado, permitindo navegação entre telas sem interferência ou vazamento de variáveis temporárias entre rotas.

#### Scenario: Alternância entre páginas
- **WHEN** o usuário navega da Central de Candidaturas para o Assistente de Nova Otimização
- **THEN** o estado de visualização de currículo individual não afeta os campos limpos do novo assistente
