# Spec Delta

## Purpose
Adiciona regras de otimização de ATS na geração de currículos para garantir leitura por sistemas automatizados.

## ADDED Requirements

### Requirement: Aplicar padrões ATS no currículo
O sistema SHALL estruturar o currículo gerado usando cabeçalhos padronizados e verbos de ação para maximizar compatibilidade com ferramentas de ATS.

#### Scenario: Formatação com ATS
- **WHEN** o currículo é gerado
- **THEN** ele contém seções exatas como 'Resumo Profissional' e 'Experiência Profissional', integrando palavras-chave da vaga naturalmente.
