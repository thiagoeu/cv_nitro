# Tasks

## 1. Endurecimento do Banco de Dados & RLS do Supabase

- [x] 1.1 Atualizar `supabase_schema.sql` com políticas RLS rigorosas (`auth.uid() = user_id`), trigger automático `on_auth_user_created` para inicializar perfis e script idempotente de migração.
- [x] 1.2 Atualizar `src/core/db_migrator.py` e seus testes em `tests/test_db_migrator.py` para fornecer instruções amigáveis de execução da migração no painel do Supabase.

## 2. Barra de Navegação Superior & Gestão de Erros (`src/ui/navbar.py`)

- [x] 2.1 Implementar `src/ui/navbar.py` renderizando o cabeçalho superior no padrão SaaS com logotipo `🎯 GitMatch CV Nitro`, abas de navegação horizontal, badge de status do usuário e função utilitária `clear_transient_state()` para purgar erros antigos.
- [x] 2.2 Criar `tests/test_navbar.py` validando o roteamento da barra de navegação, persistência da página ativa e limpeza de erros transitórios.

## 3. Telas Dedicadas de Autenticação (`src/ui/auth_views.py`)

- [x] 3.1 Implementar `src/ui/auth_views.py` com páginas dedicadas e focadas para Login e Cadastro, validações de senha, opção "Entrar como Convidado" e mensagens contextuais de erro.
- [x] 3.2 Criar `tests/test_auth_views.py` validando a renderização e submissão dos formulários de login e cadastro.

## 4. Modularização da Camada Visual (`src/ui/`)

- [x] 4.1 Implementar `src/ui/wizard_view.py` desacoplando o assistente em 3 etapas com auto-preenchimento de perfil e limpeza prévia de alertas antes de disparar o grafo.
- [x] 4.2 Implementar `src/ui/dashboard_view.py` desacoplando cards de métricas, gráficos de distribuição de tecnologias e idiomas.
- [x] 4.3 Implementar `src/ui/applications_view.py` desacoplando a tabela de histórico com busca reativa e o visualizador detalhado de currículo (A4/PDF, Markdown puro e Carta).
- [x] 4.4 Implementar `src/ui/settings_view.py` desacoplando a edição de perfil, cache de repositórios do GitHub e diagnóstico de conexão do banco de dados.

## 5. Roteador Desacoplado (`app.py`) & Validação Final

- [x] 5.1 Refatorar `app.py` para atuar como roteador limpo e conciso (< 100 linhas), delegando todas as rotas para os módulos especializados em `src/ui/`.
- [x] 5.2 Executar suíte completa de testes (`pytest`) garantindo que todos os testes passem com 100% de sucesso e sem regressões.
