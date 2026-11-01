# Tasks: Proteção de Rotas e Landing Page Pública para Visitantes

## 1. Landing Page Pública

- [x] 1.1 Criar o módulo `src/ui/landing_view.py` com Hero Section contendo badge de IA, título de impacto ("Com o CV-Nitro, você se destaca em qualquer processo seletivo tech"), subtítulo persuasivo e botões de CTA ("Criar Conta Grátis" e "Já tenho conta / Entrar").
- [x] 1.2 Implementar seções explicativas na landing page: grid com 4 cards de recursos (Análise de Vagas, Otimização de Currículos, Score ATS e Carta de Apresentação), passo a passo de como funciona em 3 etapas e card de fechamento com CTAs adicionais.
- [x] 1.3 Adicionar testes unitários de renderização da landing page em `tests/test_ui.py` e verificar aprovação com `pytest`.

## 2. Controle de Acesso e Proteção de Rotas

- [x] 2.1 Adicionar a página `landing` no catálogo de páginas (`PAGES`) em `src/ui/navbar.py` e separar claramente as rotas públicas (`landing`, `login`, `signup`) das rotas privadas (`dashboard`, `wizard`, `applications`, `profile`, `settings`, `logout`).
- [x] 2.2 Implementar guarda de rotas em `render_navbar`: quando `is_guest` for `True`, configurar `st.navigation` com as opções públicas e definir `landing` como página padrão, impedindo que o visitante visualize ou execute páginas privadas.
- [x] 2.3 Configurar o menu completo para usuários autenticados (`is_guest=False`), mantendo o `dashboard` como página padrão e exibindo as ferramentas internas e menu de conta com perfil, configurações e logout.

## 3. Redirecionamento Pós-Autenticação e Roteamento Principal

- [x] 3.1 Atualizar `src/ui/auth_views.py` para redirecionar explicitamente para o `dashboard` (`set_page("dashboard")`) após login ou cadastro com sucesso.
- [x] 3.2 Atualizar `render_logout_view` em `src/ui/auth_views.py` para redirecionar para a `landing` page pública (`set_page("landing")`) ao encerrar a sessão.
- [x] 3.3 Atualizar `app.py` para registrar a view `landing` no dicionário de visualizações do `render_navbar` e verificar integridade da inicialização do app.

## 4. Testes e Validação Integrada

- [x] 4.1 Expandir os testes em `tests/test_ui.py` cobrindo comportamento da navbar para visitante (rotas restritas a público), para usuário autenticado (rotas completas) e redirecionamento de login/logout.
- [x] 4.2 Executar a suíte completa de testes com `pytest` e verificar que todos os testes passam sem regressões.
- [x] 4.3 Validar no navegador o acesso deslogado (exibição da Landing Page e ausência de abas privadas) e a navegação pós-login.
