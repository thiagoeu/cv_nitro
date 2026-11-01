# Spec Delta: auth-access-control

## Purpose

Define as regras de proteção de rotas privadas, controle de acesso para visitantes não autenticados e a experiência de apresentação institucional através de uma Landing Page pública de alto impacto no CV-Nitro.

## ADDED Requirements

### Requirement: Private Route Protection for Unauthenticated Guests
O sistema SHALL bloquear o acesso de usuários visitantes não autenticados a quaisquer rotas e recursos privados da aplicação (`dashboard`, `wizard`, `applications`, `profile`, `settings`), redirecionando tentativas não autorizadas para a página pública inicial ou tela de autenticação com aviso informativo.

#### Scenario: Guest attempts direct access to private route
- **WHEN** um usuário não autenticado tentar navegar diretamente ou tiver como rota ativa uma tela privada
- **THEN** o sistema SHALL impedir a execução da tela privada e redirecionar o usuário para a Landing Page pública ou tela de login exibindo orientação de acesso

#### Scenario: Authenticated user accesses private routes
- **WHEN** um usuário com sessão autenticada ativa acessar qualquer rota privada autorizada
- **THEN** o sistema SHALL renderizar a respectiva funcionalidade normalmente

### Requirement: Public Navigation Bar for Guest Users
O sistema SHALL exibir na barra de navegação superior exclusivamente as páginas públicas permitidas ("Início", "Entrar", "Criar conta") enquanto o usuário estiver no estado visitante/desconectado, ocultando todos os links das ferramentas privadas e menus de conta restritos.

#### Scenario: Unauthenticated visitor views top navigation
- **WHEN** a barra de navegação superior for renderizada para um usuário não autenticado
- **THEN** a barra SHALL exibir somente os links públicos ("Início", "Entrar", "Criar conta") e ocultar atalhos para Dashboard, Otimizador, Candidaturas, Perfil e Sistema

#### Scenario: Authenticated user views full navigation
- **WHEN** a barra de navegação superior for renderizada para um usuário com login ativo
- **THEN** a barra SHALL exibir os links principais ("Dashboard", "Otimizador", "Candidaturas", "Perfil") e o menu de conta com perfil e opção "Sair"

### Requirement: High-Impact Public Landing Page
O sistema SHALL renderizar uma Landing Page institucional moderna como página padrão para usuários visitantes, apresentando a proposta de valor do CV-Nitro, pilares de diferenciação por agentes de IA e botões de chamada para ação (CTAs) para cadastro e login.

#### Scenario: Visitor views default landing page
- **WHEN** um usuário não autenticado acessa a aplicação
- **THEN** o sistema SHALL exibir a Landing Page com proposta de valor ("Com o CV-Nitro, você se destaca em qualquer processo seletivo tech"), cards com benefícios da IA e CTAs proeminentes de conversão

#### Scenario: Visitor clicks Create Account CTA
- **WHEN** o visitante clica no botão "Criar Conta Grátis" na Landing Page
- **THEN** o sistema SHALL direcionar imediatamente para a tela de cadastro (`signup`)

#### Scenario: Visitor clicks Login CTA
- **WHEN** o visitante clica no botão "Já tenho conta / Entrar" na Landing Page
- **THEN** o sistema SHALL direcionar imediatamente para a tela de login (`login`)

### Requirement: Post-Authentication Redirection
O sistema SHALL redirecionar o usuário automaticamente para o painel principal (`dashboard`) imediatamente após a conclusão bem-sucedida de um login ou cadastro de conta, atualizando os privilégios da sessão.

#### Scenario: Successful login transitions to private dashboard
- **WHEN** o usuário submete credenciais válidas na tela de login
- **THEN** a sessão é marcada como autenticada e o sistema redireciona a interface para o `dashboard` com navegação interna liberada

#### Scenario: Successful signup transitions to private dashboard
- **WHEN** o usuário cria uma nova conta com sucesso
- **THEN** a sessão é inicializada como autenticada e o sistema redireciona a interface para o `dashboard`
