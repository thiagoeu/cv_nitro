# resume-history Specification

## Purpose
Permite que o usuário acesse, visualize e gerencie todos os currículos otimizados gerados anteriormente.

## Requirements

### Requirement: Listar currículos gerados
O sistema SHALL exibir uma lista de todos os currículos salvos no histórico associados ao `user_id` do usuário conectado, ordenados da data mais recente à mais antiga.

#### Scenario: Visualização do histórico vazio
- **WHEN** não há currículos salvos para o usuário atual no histórico
- **THEN** o sistema exibe uma mensagem indicando que o histórico está vazio

#### Scenario: Visualização do histórico com itens
- **WHEN** há currículos salvos pertencentes ao usuário logado
- **THEN** o sistema lista os currículos com seus respectivos títulos da vaga, idioma, score ATS e data formatada

### Requirement: Carregar currículo salvo
O sistema SHALL carregar e exibir o conteúdo Markdown de um currículo ao ser selecionado no histórico.

#### Scenario: Seleção de currículo
- **WHEN** o usuário clica em um currículo específico na aba de histórico
- **THEN** o conteúdo completo do currículo é exibido na tela principal para cópia e leitura

### Requirement: Armazenamento e recuperação de Cover Letter
O sistema SHALL persistir a Cover Letter gerada junto com o currículo no registro histórico e permitir a recuperação individual de ambos os documentos.

#### Scenario: Carregamento de aplicação com Cover Letter
- **WHEN** o usuário seleciona uma candidatura gravada no histórico
- **THEN** o sistema carrega tanto o currículo ajustado quanto a respectiva carta de apresentação

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
