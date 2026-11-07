# modular-ui-architecture Specification

## Purpose
Estabelece a divisão modular da interface em componentes de responsabilidade única no diretório src/ui, desacoplando roteamento, autenticação, formulários e visualizações analíticas.

## Requirements

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

### Requirement: Separação entre tema visual, componentes reutilizáveis e sub-painéis de visualização
O sistema SHALL isolar definições de folhas de estilo CSS globais e tokens de tema em módulo dedicado, mantendo os componentes interativos e os sub-painéis de edição/re-otimização de candidaturas em módulos separados de responsabilidade única.

#### Scenario: Carregamento desacoplado de estilos e componentes
- **WHEN** a interface inicializa o tema visual ou renderiza componentes reutilizáveis e abas de candidatura
- **THEN** as definições de estilo global, os widgets interativos e os sub-painéis de edição/re-otimização operam a partir de módulos especializados mantendo contratos de importação retrocompatíveis

### Requirement: Modularização de formatação de documentos, armazenamento e validação determinística
O sistema SHALL organizar a formatação de currículos (estilos A4, parser Markdown e renderizador HTML), o armazenamento local/híbrido e a validação determinística ATS em subpacotes e módulos coesos, preservando fachadas públicas compatíveis nos caminhos originais de importação.

#### Scenario: Importação retrocompatível em fachadas de domínio
- **WHEN** módulos consumidores ou testes automatizados importam funções pelos caminhos de fachada originais
- **THEN** as chamadas são delegadas transparentemente aos submódulos especializados sem alteração de comportamento funcional
