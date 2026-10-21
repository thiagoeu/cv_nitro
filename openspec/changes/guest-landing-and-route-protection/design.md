# Design: Proteção de Rotas e Landing Page Pública para Visitantes

## Context

A aplicação utiliza Streamlit 1.39+ com `st.navigation` configurado em `src/ui/navbar.py`. O estado de autenticação é gerido via `st.session_state.user_session` (criado por `auth_manager.create_guest_session()` quando não logado, com a flag `is_guest: True`).
Anteriormente, todas as páginas (`dashboard`, `wizard`, `applications`, `profile`, `settings`) ficavam visíveis e navegáveis para visitantes anônimos.
Esta especificação introduz um controle estrito de rotas com base na flag `is_guest` e disponibiliza uma Landing Page pública institucional para recepção e conversão de novos usuários.

## Goals / Non-Goals

**Goals:**
- Proteger 100% das páginas internas da aplicação (`dashboard`, `wizard`, `applications`, `profile`, `settings`), impedindo acesso direto ou acidental de visitantes não autenticados.
- Apresentar uma Landing Page pública de alto nível visual, moderna e persuasiva, destacando a proposta de valor do CV-Nitro no padrão de cores 60-30-10.
- Exibir botões claros e convidativos de Call to Action (CTA) direcionando para cadastro (`signup`) e login (`login`).
- Fornecer menu superior adaptativo:
  - Visitantes: apenas "Início" (Landing), "Entrar" (Login) e "Criar conta" (Signup).
  - Usuários autenticados: "Dashboard", "Otimizador", "Candidaturas", "Perfil" e menu de conta com "Sistema" e "Sair".
- Redirecionar automaticamente para o Dashboard após login ou registro bem-sucedido.
- Manter 100% dos testes unitários passando.

**Non-Goals:**
- Não alterar regras de negócio dos agentes LangGraph ou lógica de banco de dados Supabase.
- Não restringir acesso a assets públicos (como `assets/logo.svg`).

## Decisions

### Decisão 1: Separação de Catálogo de Páginas por Permissão
- **Abordagem**: Em `src/ui/navbar.py`, o dicionário de páginas passadas para `st.navigation` será bifurcado de acordo com `session.get("is_guest", True)`:
  - Para `is_guest == True`: rotas expostas serão apenas `landing`, `login` e `signup`. A página padrão (`default=True`) é a `landing`.
  - Para `is_guest == False`: rotas expostas serão `dashboard`, `wizard`, `applications`, `profile`, `settings` e `logout`. A página padrão (`default=True`) é o `dashboard`.
- **Alternativa Descartada**: Manter todas as páginas registradas em `st.navigation` com `visibility="hidden"`. Ocultar apenas o link visual no menu não impede que a rota seja executada caso o Streamlit tente renderizar a rota padrão ou um link direto na URL. A bifurcação do conjunto de páginas ativas em `st.navigation` garante proteção determinística nativa.

### Decisão 2: Guarda de Rota e Interceptação Segura
- **Abordagem**: Implementar verificação de segurança na inicialização do fluxo em `src/ui/navbar.py` / `app.py`. Se `is_guest == True` e `current_page` tentar apontar para uma rota protegida (ex: `dashboard`, `wizard`, etc.), o sistema forçará a rota para `landing` (ou exibirá aviso amigável se foi navegação forçada) antes da renderização.
- **Alternativa Descartada**: Exibir página em branco ou erro 403 bruto. Um redirecionamento suave para a Landing Page melhora a experiência do visitante e estimula o cadastro.

### Decisão 3: Criação de Módulo Dedicado `src/ui/landing_view.py`
- **Abordagem**: Modularizar a landing page em um novo arquivo `src/ui/landing_view.py`, estruturado em seções:
  1. *Hero*: Título impactante ("Com o CV-Nitro, você se destaca em qualquer processo seletivo tech"), subtítulo explicativo e CTAs primário ("Criar Conta Grátis") e secundário ("Já tenho conta / Entrar").
  2. *Grid de Recursos*: 4 cards de valor com ícones e métricas (Análise de Vagas, Otimização de Experiências, Score ATS e Cartas de Apresentação).
  3. *Como Funciona*: Passo a passo simplificado em 3 etapas.
  4. *Banner Final de Conversão*: Chamada para ação final de fechamento.
- **Alternativa Descartada**: Embutir a landing page dentro de `app.py` ou `dashboard_view.py`, o que poluiria os arquivos existentes e feriria a separação de responsabilidades modular da UI.

### Decisão 4: Redirecionamento Pós-Autenticação para Dashboard
- **Abordagem**: Em `src/ui/auth_views.py`, ao concluir o login ou registro com sucesso, chamar explicitamente `set_page("dashboard")` antes de `st.rerun()`. No logout, chamar `set_page("landing")`.

## Risks / Trade-offs

- **[Risco] Sessão expirada ou visitante acessando URL antiga de dashboard**:
  - *Mitigação*: O `render_navbar` verifica se `current_page` é privada enquanto `is_guest` é True; se for, limpa o alvo e define `landing` como página corrente.
- **[Risco] Quebra em testes existentes que assumem `current_page="dashboard"` por padrão em sessão guest**:
  - *Mitigação*: Atualizar as asserções de teste para validar que o estado inicial de visitante direciona para `landing`, e simular sessão autenticada (`is_guest=False`) nos testes de visualização do dashboard.

## Migration Plan

1. Criar `src/ui/landing_view.py`.
2. Atualizar `src/ui/navbar.py` com o catálogo de rotas públicas vs. privadas e lógica de proteção.
3. Atualizar `src/ui/auth_views.py` para redirecionar para `dashboard` após autenticação e `landing` após logout.
4. Atualizar `app.py` para injetar a view `landing` no roteador.
5. Atualizar e expandir a suíte de testes em `tests/test_ui.py`.
6. Validar com `pytest` e inspecionar visualmente na interface.
