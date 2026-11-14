# Spec Delta: user-profile-reuse

## MODIFIED Requirements

### Requirement: Cache de repositórios do GitHub para economia de tokens
O sistema SHALL armazenar em cache os metadados e resumos dos repositórios do GitHub do usuário, evitando requisições externas repetitivas e reprocessamento massivo de tokens, permitindo atualização forçada sob demanda.

#### Scenario: Reutilização de repositórios em nova candidatura
- **WHEN** o usuário executa uma otimização com o mesmo usuário do GitHub já consultado anteriormente sem solicitar atualização forçada
- **THEN** o agente utiliza os dados de repositórios já presentes no cache de perfil do usuário em vez de realizar varredura completa da API do GitHub

#### Scenario: Atualização forçada via solicitação explícita
- **WHEN** o usuário solicita a sincronização forçada ou ativa a opção de atualizar repositórios antes da geração
- **THEN** o agente ignora os repositórios cacheados, consulta a API do GitHub para obter a lista atualizada e regrava o cache de perfil do usuário

## ADDED Requirements

### Requirement: Transparência e sincronização de repositórios no assistente de candidatura
O assistente de candidatura SHALL exibir a quantidade de repositórios atualmente presentes em cache e disponibilizar mecanismo de sincronização rápida sem exigir navegação até a aba de perfil.

#### Scenario: Exibição do contador de repositórios e ação de sincronização no formulário
- **WHEN** o usuário acessa o formulário de otimização de vaga ou currículo geral com usuário do GitHub preenchido
- **THEN** a interface exibe a contagem de repositórios cacheados e disponibiliza um botão de sincronização imediata que atualiza os projetos antes do início da geração

