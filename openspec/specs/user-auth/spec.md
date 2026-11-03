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
O sistema SHALL fornecer a opção de logout no menu de conta para encerrar a sessão ativa do usuário. Uma sessão encerrada MUST NOT ser restaurada por credenciais guardadas no navegador até que o usuário faça um novo login.

#### Scenario: Logout de usuário autenticado
- **WHEN** o usuário clica em Sair no menu de conta
- **THEN** o sistema finaliza a sessão, remove a credencial de sessão do navegador, limpa o estado de usuário e redireciona para a página inicial

#### Scenario: Interação após logout de sessão restaurada
- **WHEN** o usuário recarrega a página com a sessão ativa, clica em Sair e em seguida interage com qualquer elemento da página
- **THEN** o usuário permanece como visitante e não tem acesso às páginas privadas

### Requirement: Páginas dedicadas de login e cadastro
O sistema SHALL disponibilizar telas independentes e dedicadas para login e cadastro de usuários, permitindo alternar de modo intuitivo e focado.

#### Scenario: Acesso à página de login
- **WHEN** o usuário não autenticado clica em Entrar na barra superior
- **THEN** a tela de login dedicada é renderizada com campos de e-mail e senha e link para cadastro

#### Scenario: Acesso à página de cadastro
- **WHEN** o usuário clica em Criar Conta na barra superior ou na tela de login
- **THEN** a tela de cadastro dedicada é renderizada com campos de nome, e-mail e senha

### Requirement: Proteção de dados com RLS no banco
O sistema SHALL impedir que a chave pública (anon) do banco leia ou grave candidaturas e perfis, e o servidor MUST restringir toda leitura, gravação e exclusão ao `user_id` da sessão autenticada.

#### Scenario: Acesso a dados autenticados com RLS
- **WHEN** um usuário autenticado consulta suas candidaturas e perfil
- **THEN** o retorno contém exclusivamente as linhas pertencentes ao seu `user_id`

#### Scenario: Acesso direto com a chave pública
- **WHEN** alguém consulta as tabelas de candidaturas ou de perfis diretamente na API do banco usando a chave anon
- **THEN** nenhuma linha é retornada e nenhuma gravação é aceita

#### Scenario: Candidatura de outro usuário
- **WHEN** a sessão de um usuário solicita carregar ou excluir uma candidatura cujo dono é outro usuário
- **THEN** a candidatura não é retornada nem excluída

### Requirement: Token de sessão assinado com expiração
O sistema SHALL manter a sessão entre recarregamentos apenas por meio de um token assinado com um segredo obrigatório do servidor, com validade máxima de 30 dias e sem credenciais do provedor de autenticação em seu conteúdo.

#### Scenario: Inicialização sem segredo configurado
- **WHEN** a aplicação inicia sem o segredo de assinatura de sessão configurado
- **THEN** a aplicação exibe uma mensagem de configuração ausente e não atende nenhuma página

#### Scenario: Token expirado
- **WHEN** o navegador apresenta um token de sessão com validade vencida
- **THEN** a sessão não é restaurada e o usuário é tratado como visitante

#### Scenario: Token adulterado
- **WHEN** o navegador apresenta um token cujo conteúdo não corresponde à assinatura
- **THEN** a sessão não é restaurada e o usuário é tratado como visitante

#### Scenario: Token informado na URL
- **WHEN** um token de sessão válido é informado como parâmetro na URL
- **THEN** o sistema ignora o parâmetro e não restaura sessão a partir dele

### Requirement: Isolamento de sessões entre usuários
O sistema SHALL manter o estado de autenticação de cada usuário isolado, de modo que login, logout ou expiração de um usuário não altere o acesso aos dados de outro usuário conectado ao mesmo servidor.

#### Scenario: Usuários simultâneos no mesmo servidor
- **WHEN** o usuário A está conectado e o usuário B faz login no mesmo servidor
- **THEN** as candidaturas salvas por A continuam vinculadas a A e são persistidas na nuvem

#### Scenario: Logout de outro usuário
- **WHEN** o usuário B faz logout enquanto o usuário A está conectado
- **THEN** o usuário A continua acessando e gravando seus próprios dados sem interrupção

### Requirement: Autenticação local de desenvolvimento
Quando o banco em nuvem não estiver configurado, o sistema SHALL identificar cada conta local por um `user_id` derivado do e-mail informado e MUST exibir aviso de que o modo local não verifica senha.

#### Scenario: Contas locais distintas
- **WHEN** dois e-mails diferentes fazem login no modo local
- **THEN** cada um vê apenas as próprias candidaturas e o próprio perfil

#### Scenario: Aviso de modo local
- **WHEN** a tela de login ou cadastro é exibida sem banco em nuvem configurado
- **THEN** a tela mostra aviso de modo de desenvolvimento sem verificação de senha
