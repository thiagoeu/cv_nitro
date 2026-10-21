# Proposal

## Why

A experiência atual do GitMatch concentra toda a navegação em um seletor vertical por botão de rádio na barra lateral, conferindo um aspecto visual amador que se assemelha a opções de formulário ("checkbox") em vez de um produto web moderno (SaaS). Além disso, o arquivo `app.py` acumulou centenas de linhas misturando roteamento, autenticação, formulários, renderização de gráficos e persistência, gerando alto acoplamento e dificultando a manutenção. Ao mesmo tempo, mensagens de erro e alertas de execuções anteriores persistem na tela mesmo quando o usuário inicia uma nova busca, gerando poluição visual.

Esta mudança moderniza a arquitetura visual e técnica da aplicação, introduzindo uma barra de navegação superior padronizada com logotipo, telas dedicadas para Login/Cadastro, roteamento desacoplado em módulos de UI independentes (`src/ui/`), ciclo de vida limpo para mensagens de erro e um guia detalhado com script SQL consolidado para habilitar de fato a autenticação protegida por RLS (`auth.uid() = user_id`) no Supabase.

## What Changes

- **Barra de Navegação Superior (Header / Navbar)**:
  - Criação de componente visual moderno no topo (`src/ui/navbar.py`) contendo Logo `🎯 GitMatch CV Nitro`, links estilizados de navegação entre seções e área de usuário/perfil no canto superior direito.
  - Substituição definitiva do botão de rádio vertical ("checkbox") da sidebar por navegação orientada a abas/rotas visualmente atraentes e responsivas.
  - Sidebar preservada exclusivamente para Acesso Rápido a currículos recentes e utilitários.

- **Telas Dedicadas de Autenticação (Login & Cadastro)**:
  - Criação de página/módulo dedicado (`src/ui/auth_view.py`) para Login e Registro em tela limpa, com design focado, validações de formulário e opção de acesso rápido como visitante.

- **Desacoplamento e Modularização da UI**:
  - Divisão de `app.py` em módulos especializados em `src/ui/`:
    - `src/ui/navbar.py`: barra superior, logo e status de autenticação.
    - `src/ui/auth_view.py`: telas de login e cadastro.
    - `src/ui/wizard_view.py`: assistente de otimização em 3 etapas com auto-preenchimento.
    - `src/ui/dashboard_view.py`: painel de métricas executivas e gráficos.
    - `src/ui/applications_view.py`: listagem e detalhe/impressão de currículos.
    - `src/ui/settings_view.py`: gestão de perfil, cache de projetos e status do Supabase.
  - `app.py` passa a atuar estritamente como roteador enxuto e inicializador de estado.

- **Tratamento e Ciclo de Vida Limpo de Mensagens de Erro**:
  - Implementação de utilitário `clear_transient_state()` executado antes de cada nova busca, login ou otimização, garantindo que alertas antigos não fiquem visíveis na tela.
  - Exibição de erros de forma limpa através de toasts ou banners contextuais não-persistentes.

- **Endurecimento e Atualização do Supabase Auth**:
  - Consolidação do script `supabase_schema.sql` com políticas RLS estritas onde `user_id = auth.uid()`.
  - Trigger automático em PostgreSQL para inicializar a linha do usuário em `user_profiles` assim que ele se cadastrar no `auth.users`.
  - Documentação passo a passo no painel de configurações para aplicar a migration com 1 clique no SQL Editor do Supabase.

## Capabilities

### New Capabilities
- `site-navigation`: Barra superior moderna com logotipo, navegação por abas/rotas SaaS, área de usuário no topo e ciclo de vida limpo para erros e feedbacks.
- `modular-ui-architecture`: Estruturação desacoplada da camada de apresentação em componentes especializados em `src/ui/`, mantendo `app.py` como roteador enxuto.
- `user-auth`: Telas dedicadas e separadas para Login e Cadastro, validações com limpeza de estado transitório e proteção definitiva de dados com RLS no Supabase.

### Modified Capabilities


## Impact

- **Frontend / Interface**: `app.py` é refatorado para menos de 100 linhas, delegando a renderização para componentes em `src/ui/`.
- **Experiência do Usuário (UX)**: Design com padrão de mercado (navbar superior, logo, páginas dedicadas de login), sem sensação de botões de formulário para navegar.
- **Banco de Dados (Supabase)**: `supabase_schema.sql` enriquecido com trigger `handle_new_user()` e políticas RLS de segurança baseadas em sessão autenticada.
- **Manutenibilidade**: Código 100% desacoplado, facilitando testes e futuras expansões sem regressões de lógica de agentes.
