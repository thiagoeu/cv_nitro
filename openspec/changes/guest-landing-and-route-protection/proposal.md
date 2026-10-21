# Proposal: Proteção de Rotas e Landing Page Pública para Visitantes

## Why

Atualmente, qualquer usuário não autenticado (visitante/guest) consegue acessar e visualizar todas as áreas internas do sistema (Dashboard, Otimizador de Currículos, Histórico de Candidaturas, Perfil e Configurações). Além de expor telas internas sem autenticação prévia, o visitante não é recebido com uma apresentação comercial ou institucional dos benefícios da plataforma.

Esta mudança protege todas as rotas privadas do CV-Nitro, impedindo o acesso de usuários deslogados a qualquer recurso interno, e introduz uma Landing Page pública de alto impacto que divulga o produto com chamada persuasiva e botões diretos de ação (Entrar e Criar Conta).

## What Changes

- **Proteção Estrita de Rotas**: Usuários não logados têm acesso bloqueado a todas as páginas privadas (`dashboard`, `wizard`, `applications`, `profile`, `settings`). Tentativas de navegação não autorizada direcionam o usuário para a tela inicial pública ou login com aviso amigável.
- **Navegação Adaptativa para Visitantes**: O menu superior para visitantes deslogados exibe exclusivamente as opções públicas: "Início" (Landing Page), "Entrar" (Login) e "Criar conta" (Cadastro). As abas de trabalho são omitidas até o login ser realizado com sucesso.
- **Landing Page Pública de Alto Impacto (`src/ui/landing_view.py`)**: Uma página inicial moderna no padrão 60-30-10 apresentando a proposta de valor do CV-Nitro ("*Com o CV-Nitro, você se destaca em qualquer processo seletivo tech*"), pilares da solução (análise multi-agente, adaptação sob medida para vagas, aderência ATS e geração de cartas), demonstrações visuais e botões destacados de CTA ("Criar Conta Grátis" e "Já tenho conta / Entrar").
- **Redirecionamento Pós-Autenticação**: Ao fazer login ou criar conta com sucesso, o usuário é imediatamente redirecionado para a aplicação interna protegida (`dashboard`), liberando o menu completo de funcionalidades.

## Capabilities

### New Capabilities
- `auth-access-control`: Regras de proteção de rotas e controle de acesso para visitantes não autenticados, com isolamento de áreas privadas e disponibilização de Landing Page institucional de conversão com CTAs de autenticação.

### Modified Capabilities
<!-- Nenhuma especificação anterior teve seus requisitos alterados; a nova capacidade complementa as existentes. -->

## Impact

- **Código Afetado**:
  - `src/ui/navbar.py`: Atualização do catálogo de páginas e regras de visibilidade/roteamento baseado no status de autenticação da sessão.
  - `src/ui/landing_view.py`: Novo módulo com o layout visual e CTAs da landing page.
  - `app.py`: Integração da rota da landing page e garantia de fallback seguro para usuários anônimos.
  - `src/ui/auth_views.py`: Ajuste para redirecionar para o dashboard após login/registro.
  - `tests/test_ui.py`: Novos testes unitários validando a proteção de rotas e o comportamento da navegação para visitantes vs. usuários autenticados.
- **APIs e Dependências**: Nenhuma dependência externa nova necessária. Utiliza os recursos nativos do Streamlit (`st.navigation`, `st.Page`, `st.session_state`).
