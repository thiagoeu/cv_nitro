# Spec Delta

## Purpose

Permite visualizar o currículo otimizado com diagramação tipográfica profissional e exportá-lo diretamente em HTML ou PDF com layout pronto para impressão.

## ADDED Requirements

### Requirement: Renderização visual em folha de estilo profissional
O sistema SHALL fornecer uma pré-visualização estilizada do currículo com tipografia proporcional, bordas sutis e estrutura correspondente a um documento físico A4.

#### Scenario: Visualização do currículo estilizado
- **WHEN** o usuário seleciona a visualização formatada do currículo
- **THEN** o sistema exibe o documento renderizado com estilo visual idêntico ao modelo de alta fidelidade

### Requirement: Exportação para impressão em PDF e HTML
O sistema SHALL permitir o download do currículo em formato HTML auto-contido com regras de CSS print para salvamento direto como PDF no navegador.

#### Scenario: Download de documento pronto para impressão
- **WHEN** o usuário clica no botão de exportar/imprimir
- **THEN** o sistema gera um arquivo com estilos de impressão configurados para gerar um PDF com formatação preservada
