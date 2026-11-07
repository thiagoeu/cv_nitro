# Spec Delta

## ADDED Requirements

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

