# Spec Delta

## Purpose

Permite persistir e reaproveitar dados do perfil do candidato (currículo base, usuário GitHub e repositórios cacheados) para acelerar novas otimizações e economizar tokens de IA.

## ADDED Requirements

### Requirement: Persistência de perfil do candidato
O sistema SHALL permitir que o usuário salve e atualize seu currículo base padrão, usuário do GitHub e informações de perfil vinculadas ao seu `user_id`.

#### Scenario: Atualização de perfil com sucesso
- **WHEN** o usuário atualiza seu currículo base e usuário do GitHub nas configurações de perfil e clica em salvar
- **THEN** o sistema grava os dados de perfil vinculados ao `user_id` no banco de dados e atualiza o estado da sessão

### Requirement: Pré-carregamento automático no assistente
O sistema SHALL pré-carregar automaticamente o currículo base e usuário do GitHub do perfil do usuário autenticado na etapa de Nova Otimização.

#### Scenario: Acesso ao Wizard de otimização por usuário logado
- **WHEN** um usuário autenticado acessa a aba de Nova Otimização
- **THEN** os campos de Currículo Base e Usuário do GitHub são preenchidos com os dados salvos do perfil, permitindo edição ou envio imediato

### Requirement: Cache de repositórios do GitHub para economia de tokens
O sistema SHALL armazenar em cache os metadados e resumos dos repositórios do GitHub do usuário, evitando requisições externas repetitivas e reprocessamento massivo de tokens.

#### Scenario: Reutilização de repositórios em nova candidatura
- **WHEN** o usuário executa uma otimização com o mesmo usuário do GitHub já consultado anteriormente
- **THEN** o agente utiliza os dados de repositórios já presentes no cache de perfil do usuário em vez de realizar varredura completa da API do GitHub
