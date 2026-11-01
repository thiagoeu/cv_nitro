# user-auth Specification

## Purpose
Gerencia autenticação simples de candidatos e visitantes, fornecendo controle de sessão seguro, cadastro, login e identificador de usuário para isolamento de dados.

## Requirements

### Requirement: Autenticação com e-mail e senha
O sistema SHALL permitir que usuários realizem login e cadastro com e-mail e senha através do provedor de autenticação configurado.

#### Scenario: Login bem-sucedido
- **WHEN** o usuário fornece credenciais válidas e clica em Entrar
- **THEN** o sistema autentica a sessão, define o `user_id` ativo no estado da aplicação e exibe o painel principal

#### Scenario: Falha de autenticação
- **WHEN** o usuário insere uma senha incorreta ou e-mail inexistente
- **THEN** o sistema exibe uma mensagem de erro clara e mantém o usuário na tela de login

### Requirement: Modo visitante e uso anônimo
O sistema SHALL permitir o uso anônimo com identificador temporário de convidado caso o usuário opte por testar a plataforma sem criar conta imediatamente.

#### Scenario: Acesso como convidado
- **WHEN** o usuário clica na opção de continuar como visitante/convidado
- **THEN** o sistema inicia uma sessão local anônima permitindo a otimização de currículos sem persistência em nuvem

### Requirement: Encerramento de sessão
O sistema SHALL fornecer a opção de logout na barra lateral para encerrar a sessão ativa do usuário.

#### Scenario: Logout de usuário autenticado
- **WHEN** o usuário clica em Sair na barra lateral
- **THEN** o sistema finaliza a sessão no cliente de autenticação, limpa o estado de usuário e redireciona para a tela de autenticação

### Requirement: Páginas dedicadas de login e cadastro
O sistema SHALL disponibilizar telas independentes e dedicadas para login e cadastro de usuários, permitindo alternar de modo intuitivo e focado.

#### Scenario: Acesso à página de login
- **WHEN** o usuário não autenticado clica em Entrar na barra superior
- **THEN** a tela de login dedicada é renderizada com campos de e-mail e senha e link para cadastro

#### Scenario: Acesso à página de cadastro
- **WHEN** o usuário clica em Criar Conta na barra superior ou na tela de login
- **THEN** a tela de cadastro dedicada é renderizada com campos de nome, e-mail e senha

### Requirement: Proteção de dados com RLS no banco
O sistema SHALL aplicar políticas de Row Level Security (RLS) no Supabase vinculando os registros ao identificador único `auth.uid() = user_id`.

#### Scenario: Acesso a dados autenticados com RLS
- **WHEN** um usuário autenticado consulta suas candidaturas e perfil
- **THEN** o banco de dados restringe o retorno exclusivamente às linhas pertencentes ao `user_id` autenticado
