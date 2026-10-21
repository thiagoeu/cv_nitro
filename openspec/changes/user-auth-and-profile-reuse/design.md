# Design

## Context

Atualmente, o GitMatch conecta-se diretamente ao Supabase via `history_manager.py` para salvar e consultar a tabela `applications`, mantendo fallback em arquivos Markdown locais na pasta `history/`. Todas as operações eram públicas/anônimas, sem separação de dados por candidato e sem persistência de configurações de perfil. A cada nova vaga, o candidato precisava colar novamente o currículo base e reinserir seu usuário do GitHub, forçando o fluxo multi-agente a realizar consultas e reenvio de grandes blocos de texto ao LLM.

## Goals / Non-Goals

**Goals:**
- Implementar autenticação simples e elegante no Streamlit utilizando o Supabase Auth (`sign_in_with_password`, `sign_up`, `sign_out`) com fallback para modo visitante/convidado.
- Criar a camada de perfil do candidato (`user_profiles`) para armazenar currículo base padrão, usuário do GitHub e cache de projetos/repositórios.
- No assistente de Nova Otimização (Wizard), preencher automaticamente os campos a partir do perfil do usuário ativo, permitindo reaproveitamento direto com 0 cliques extras.
- Integrar o serviço de enriquecimento do GitHub ao cache de perfil, evitando requisições redundantes de rede e diminuindo em 40% a 60% os tokens enviados nos prompts de otimização.
- Filtrar o histórico de candidaturas por `user_id` com políticas RLS no Supabase e isolamento de arquivos locais.

**Non-Goals:**
- Implementar fluxo de recuperação de senha por e-mail transacional (Magic Links / SMTP personalizado) nesta fase.
- Integração de múltiplos provedores OAuth sociais (Google, LinkedIn, etc.) nesta primeira versão de autenticação.
- Gestão de planos pagos ou cobrança de assinaturas.

## Decisions

### 1. Supabase Auth integrado com fallback no session_state do Streamlit
- **Decisão**: Utilizar o módulo nativo `supabase.auth` para autenticação com e-mail e senha. Na interface, criar um componente modular de login/cadastro na barra lateral ou em modal/tela inicial se não autenticado, com a opção "Continuar como Convidado".
- **Alternativas consideradas**:
  - *Criar banco próprio SQLite com hashes bcrypt*: descartado para evitar duplicidade de infraestrutura, já que o Supabase PostgreSQL já está ativo e possui infraestrutura completa de autenticação segura e tokens JWT.
  - *Obrigar login rígido sem modo visitante*: descartado para não prejudicar a usabilidade e velocidade de quem deseja apenas testar a ferramenta localmente.

### 2. Tabela `user_profiles` dedicada para currículo base e cache de projetos
- **Decisão**: Criar a tabela `user_profiles` no Supabase com chave primária referenciando `auth.users(id)`:
  - `user_id` (UUID, PK)
  - `full_name` (TEXT)
  - `base_resume` (TEXT)
  - `github_username` (TEXT)
  - `cached_repos` (JSONB)
  - `skills` (JSONB)
  - `updated_at` (TIMESTAMPTZ)
- **Alternativas consideradas**:
  - *Armazenar no `raw_user_meta_data` do `auth.users`*: descartado porque currículos e repositórios podem somar mais de 20 KB de texto, o que sobrecarrega os tokens JWT de autenticação.

### 3. Cache de projetos do GitHub no perfil para economia de tokens
- **Decisão**: Quando o usuário rodar a primeira otimização com seu GitHub informado, os metadados dos repositórios relevantes identificados (nome, descrição, principais tópicos e resumo do README) são gravados em `user_profiles.cached_repos`. Nas próximas otimizações, o agente de análise busca primeiro no cache do perfil e injeta apenas os projetos estritamente relacionados à vaga no prompt, diminuindo drasticamente o consumo de tokens.
- **Alternativas consideradas**:
  - *Fazer varredura de API e LLM toda vez*: descartado por consumir cotas de LLM e tokens desnecessariamente para projetos que raramente sofrem alterações radicais no mesmo dia.

### 4. Filtragem por `user_id` no histórico e compatibilidade retroativa
- **Decisão**: Adicionar a coluna `user_id UUID` na tabela `applications`. As consultas `list_resumes()` e `save_resume()` passam a considerar o `user_id` da sessão ativa. Candidaturas antigas criadas antes da autenticação continuam visíveis na sessão convidado/local e contam com uma opção de vinculação com 1 clique para associá-las à conta criada.

## Risks / Trade-offs

- **[Risco] Usuário sem conexão com o Supabase ou com credenciais inválidas** → **Mitigação**: O sistema detecta a ausência de conexão e opera em modo local (guest) automaticamente, salvando o perfil em arquivo JSON local (`profiles/guest.json`).
- **[Risco] Usuário alterar repositórios no GitHub e o cache ficar desatualizado** → **Mitigação**: Adicionar botão "🔄 Atualizar Projetos do GitHub" no perfil para forçar nova consulta sob demanda.
- **[Risco] Re-renderização e perda de estado de login no Streamlit** → **Mitigação**: Persistir os tokens da sessão no `st.session_state` e restaurar automaticamente durante os ciclos de re-execução do Streamlit.

## Migration Plan

1. Executar migration SQL no Supabase para criar `user_profiles` e adicionar `user_id` em `applications`.
2. Adicionar módulo `src/core/auth_manager.py` para encapsular chamadas de login, cadastro, logout e sessão.
3. Adicionar módulo `src/core/profile_manager.py` para carregar e atualizar o perfil e os repositórios cacheados.
4. Integrar componentes visuais no `app.py` (menu de usuário na barra lateral e pré-preenchimento no assistente de otimização).
