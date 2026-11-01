# Design

## Context

O GitMatch atualmente possui sua navegação concentrada em um `st.sidebar.radio` vertical no menu lateral, o que confere uma aparência amadora semelhante a um conjunto de checkboxes de formulário, distante dos padrões modernos de produtos SaaS. Ao mesmo tempo, o arquivo `app.py` tornou-se um script monolítico com quase 600 linhas de código misturando renderização, persistência, roteamento, lógica de gráficos e regras de formulários. Além disso, o gerenciamento de erros não possui limpeza de estado transitório, fazendo com que mensagens de falha de tentativas anteriores permaneçam na tela após novas buscas. Por fim, o banco Supabase precisa de políticas RLS ativas vinculadas a `auth.uid()` para que o login proteja os dados de cada candidato com segurança real em nível de banco de dados.

## Goals / Non-Goals

**Goals:**
- Implementar uma barra de navegação superior moderna (`src/ui/navbar.py`) com logotipo da marca, abas horizontais estilizadas para as páginas principais e área de autenticação/perfil no canto superior direito.
- Fornecer telas dedicadas e focadas para Login e Cadastro (`src/ui/auth_view.py`), substituindo popovers comprimidos na barra lateral por uma experiência limpa de onboarding.
- Desacoplar completamente a camada visual criando componentes especializados em `src/ui/` (`wizard_view.py`, `dashboard_view.py`, `applications_view.py`, `settings_view.py`), reduzindo `app.py` a um roteador enxuto (< 90 linhas).
- Implementar controle de ciclo de vida de mensagens de erro com limpeza automática (`clear_transient_messages()`) ao iniciar novas buscas ou submissões.
- Atualizar o `supabase_schema.sql` com políticas de Row Level Security (RLS) seguras baseadas em `auth.uid() = user_id` e trigger de banco para criação automática de perfil ao cadastrar usuário.

**Non-Goals:**
- Reescrever o framework de frontend para React ou Next.js (o objetivo é levar o Streamlit ao ápice de qualidade visual e modularidade).
- Modificar o fluxo multi-agente do LangGraph em `src/agents/` ou a lógica de formatação de currículo em `src/core/resume_formatter.py`.

## Decisions

### 1. Barra Superior Moderna (Navbar) em vez de Radio Buttons na Sidebar
- **Decisão**: Criar o componente `render_navbar()` que se posiciona no topo da aplicação com:
  - Logotipo e badge da versão no lado esquerdo (`🎯 GitMatch CV Nitro`).
  - Botões de navegação horizontal com indicação visual da página ativa (`📊 Dashboard`, `🚀 Otimizador`, `📚 Candidaturas`, `⚙️ Configurações`).
  - Botão de Acesso / Perfil no lado direito (`🔑 Entrar / Cadastrar` ou `🟢 Perfil (<Nome>)` com dropdown de Logout).
  - A barra lateral (sidebar) passa a ser utilizada exclusivamente para o que foi desenhada: **⚡ Acesso Rápido** aos currículos recentes e atalhos rápidos de navegação.
- **Alternativas consideradas**:
  - *Manter radio buttons na sidebar*: descartado por ser o principal motivo da insatisfação visual do usuário.

### 2. Telas Dedicadas de Autenticação (`src/ui/auth_view.py`)
- **Decisão**: Quando o usuário clicar em "Entrar" ou "Cadastrar", a aplicação transiciona para a visualização dedicada de autenticação, renderizando um card centralizado e limpo com validações, botão de submissão e link para "Continuar como Convidado".
- **Alternativas consideradas**:
  - *Popover apertado na sidebar*: descartado porque esconde erros, comprime campos e prejudica a experiência em dispositivos móveis.

### 3. Modularização Completa em `src/ui/`
- **Decisão**: Distribuir as responsabilidades em arquivos especializados:
  - `src/ui/navbar.py`: cabeçalho superior e controle de rotas.
  - `src/ui/auth_view.py`: telas de login e registro.
  - `src/ui/wizard_view.py`: assistente em 3 etapas para nova vaga com auto-preenchimento de perfil.
  - `src/ui/dashboard_view.py`: métricas analíticas e gráficos de tecnologias/idiomas.
  - `src/ui/applications_view.py`: lista pesquisável e visualização formatada A4 / Markdown.
  - `src/ui/settings_view.py`: configurações de perfil, cache do GitHub e status das conexões.
  - `app.py`: inicialização de sessão, roteador de alto nível e despacho de views.
- **Alternativas consideradas**:
  - *Manter todas as funções em `app.py`*: descartado por ferir o princípio da responsabilidade única e dificultar testes unitários.

### 4. Limpeza Automática de Estado Transitório (`clear_transient_state`)
- **Decisão**: Criar função de limpeza que purga chaves de erro e alertas temporários do `st.session_state` sempre que o usuário:
  - Inicia uma nova busca ou filtro na central de candidaturas.
  - Clica em gerar nova otimização no Wizard.
  - Alterna entre as abas principais.
- **Alternativas consideradas**:
  - *Deixar mensagens de erro permanentes*: descartado por poluir a interface com alertas de ações passadas.

### 5. Proteção de Dados com RLS no Supabase
- **Decisão**: Atualizar o script `supabase_schema.sql` para:
  - `applications`: habilitar RLS com política `auth.uid() = user_id OR user_id IS NULL`.
  - `user_profiles`: habilitar RLS com política `auth.uid() = user_id`.
  - Criar função e trigger PostgreSQL `on_auth_user_created` que insere automaticamente um registro em `user_profiles` com o ID e e-mail do usuário recém-cadastrado no Supabase Auth.
- **Instruções no App**:
  - Exibir no painel de configurações um assistente visual para o usuário copiar o script e colar no SQL Editor do Supabase com 1 clique.

## Risks / Trade-offs

- **[Risco] Usuário perder o formulário em andamento ao navegar** → **Mitigação**: Os campos de formulário utilizam chaves com prefixo de sessão persistidas no `st.session_state`.
- **[Risco] Sessões anônimas não conseguirem acessar dados de testes** → **Mitigação**: As políticas de RLS e o backend mantêm suporte permissivo para registros anônimos locais (`guest_local`).

## Migration Plan

1. Criar os módulos da interface desacoplada dentro de `src/ui/`.
2. Refatorar `app.py` para utilizar o novo roteador modular e a barra superior.
3. Atualizar `supabase_schema.sql` com RLS estrito e trigger automático.
4. Validar e executar a suíte completa de testes (`pytest`).
