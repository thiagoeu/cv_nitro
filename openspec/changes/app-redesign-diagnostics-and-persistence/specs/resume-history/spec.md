# Spec Delta: resume-history

## ADDED Requirements

### Requirement: Suporte a persistência em nuvem com fallback
O sistema SHALL persistir as candidaturas e metadados no Supabase quando as credenciais estiverem configuradas, mantendo fallback transparente para armazenamento local em caso de ausência de configuração.

#### Scenario: Persistência com credenciais de nuvem
- **WHEN** as variáveis de ambiente do Supabase estão configuradas
- **THEN** as candidaturas e metadados são salvos e carregados a partir do banco de dados na nuvem

#### Scenario: Fallback automático local
- **WHEN** as credenciais do Supabase não estão definidas
- **THEN** o sistema salva e lê o histórico a partir do sistema de arquivos local sem gerar exceções

### Requirement: Persistência de metadados de diagnóstico
O sistema SHALL registrar o relatório de diagnóstico da otimização junto ao registro de cada candidatura.

#### Scenario: Consulta de diagnóstico de candidatura salva
- **WHEN** o usuário abre uma candidatura anterior salva no histórico
- **THEN** o painel exibe o diagnóstico e feedback que foram obtidos no momento da otimização
