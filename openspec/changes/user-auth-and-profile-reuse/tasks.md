# Tasks

## 1. Schema do Banco de Dados & Modelo de Dados

- [x] 1.1 Atualizar `supabase_schema.sql` adicionando a tabela `user_profiles` (com campos `user_id`, `full_name`, `base_resume`, `github_username`, `cached_repos`, `skills`, `updated_at`) e a coluna `user_id` na tabela `applications` com políticas RLS.
- [x] 1.2 Criar script de migração/validação que verifica a existência da tabela `user_profiles` e executa com sucesso.

## 2. Camada de Autenticação (`src/core/auth_manager.py`)

- [x] 2.1 Implementar `src/core/auth_manager.py` encapsulando as operações de `sign_in_with_password`, `sign_up`, `sign_out`, `get_current_user` e `create_guest_session` com fallback local.
- [x] 2.2 Criar `tests/test_auth_manager.py` cobrindo login bem-sucedido, falha de credenciais, logout e geração de sessão de convidado.

## 3. Camada de Perfil do Candidato & Cache de Projetos (`src/core/profile_manager.py`)

- [x] 3.1 Implementar `src/core/profile_manager.py` com funções para carregar perfil (`get_user_profile`), salvar perfil (`save_user_profile`), e atualizar cache de repositórios do GitHub (`update_cached_github_repos`).
- [x] 3.2 Criar `tests/test_profile_manager.py` validando persistência do currículo base padrão, usuário do GitHub e consulta de repositórios cacheados.

## 4. Isolamento do Histórico por Usuário (`src/core/history_manager.py`)

- [x] 4.1 Atualizar `history_manager.py` para receber `user_id: Optional[str]` em `save_resume`, `list_resumes` e `delete_application`, filtrando dados exclusivamente do usuário ativo.
- [x] 4.2 Atualizar `tests/test_history.py` para garantir que usuários distintos visualizem apenas seus próprios currículos no histórico.

## 5. Interface Streamlit & Otimização com Economia de Tokens (`app.py`)

- [x] 5.1 Implementar tela/componente de autenticação em `app.py` com opções de Login, Cadastro e "Entrar como Convidado", exibindo o usuário conectado na barra lateral.
- [x] 5.2 Adicionar painel de gerenciamento de Perfil em `⚙️ Configurações & Status`, permitindo salvar o currículo base padrão e atualizar o cache do GitHub.
- [x] 5.3 Integrar o assistente de Nova Otimização (Wizard) para pré-preencher automaticamente o currículo base e usuário do GitHub a partir do perfil ativo, e alimentar o grafo com os projetos cacheados para economia de tokens.
- [x] 5.4 Executar suíte completa de testes (`pytest`) e verificar que todos os testes passem com 100% de sucesso.
