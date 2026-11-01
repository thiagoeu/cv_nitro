# Proposal

## Why

Atualmente, o GitMatch opera sem identificação de usuário: qualquer pessoa que acessa a interface compartilha o mesmo histórico geral de candidaturas e precisa reenviar ou reescrever seu currículo base e usuário do GitHub a cada nova otimização. Além disso, para cruzar dados com repositórios externos (GitHub), o sistema realiza buscas frequentes e reenvia textos longos para os LLMs, o que eleva substancialmente o consumo de tokens e aumenta o risco de atingir o limite de taxa (cota 429). 

A implementação de um sistema simples de autenticação e gerenciamento de perfil permite salvar os dados essenciais do usuário (currículo base, projetos em destaque pré-selecionados e repositórios frequentes) e vinculá-los a um `user_id`. Dessa forma, o assistente pode reaproveitar dados já indexados diretamente por ID, eliminando buscas redundantes, isolando as candidaturas por usuário para futuro deploy multi-tenant e gerando uma economia estimada de 40% a 60% de tokens nas otimizações subsequentes.

## What Changes

- **Sistema Simples de Autenticação (Login/Registro/Sessão)**:
  - Adição de tela/modal de login simples integrada ao Supabase Auth (com e-mail e senha) e fallback local em modo desenvolvimento.
  - Armazenamento do estado do usuário autenticado no `st.session_state` (`user_id`, `email`, `display_name`).
  - Opção de "Entrar como Convidado" (modo anônimo/local) para não bloquear o uso rápido.
  - Botão de logout e identificação do usuário logado na barra lateral.

- **Perfil do Candidato & Cache de Projetos/Currículo (Reaproveitamento de Dados)**:
  - Criação de uma tabela `user_profiles` no Supabase (e fallback JSON local) para persistir:
    - Currículo base padrão do usuário.
    - Usuário GitHub vinculado.
    - Lista de projetos/repositórios preferenciais e histórico de skills.
  - No assistente de otimização (Wizard), os dados do perfil salvo são carregados automaticamente por ID, permitindo ao usuário reutilizar ou refinar seu currículo base sem precisar refazer uploads ou novas pesquisas completas.
  - No agente de enriquecimento do GitHub, se os metadados dos repositórios do usuário já estiverem salvos no perfil, o sistema usa o cache em vez de disparar chamadas externas e prompts longos.

- **Isolamento de Histórico por Usuário**:
  - A tabela `applications` e as listagens de histórico passam a registrar e filtrar candidaturas pelo `user_id` do usuário conectado.
  - Políticas RLS (Row Level Security) no Supabase para garantir isolamento seguro entre contas.

## Capabilities

### New Capabilities
- `user-auth`: Gerenciamento de login, cadastro, logout e sessão de usuário (Supabase Auth com fallback local/anônimo).
- `user-profile-reuse`: Persistência de perfil do candidato (currículo base padrão, dados de GitHub e projetos cacheados) para reutilização direta por ID nas novas otimizações, economizando tokens.

### Modified Capabilities
- `resume-history`: O histórico de candidaturas passa a ser filtrado e associado ao `user_id` da sessão ativa, garantindo isolamento de registros por usuário.

## Impact

- **Banco de Dados (Supabase)**: Nova tabela `user_profiles` e adição da coluna `user_id` (UUID referenciando `auth.users`) na tabela `applications`, com ativação de RLS (Row Level Security).
- **Interface (app.py)**: Nova etapa/barra de login e exibição do usuário ativo, além de carregamento automático dos dados do perfil no Wizard de Otimização.
- **Núcleo de Histórico & Agentes**: Adaptação de `history_manager.py` e `github_service.py` para aceitar `user_id` e consultar o cache de projetos do perfil antes de buscar informações adicionais.
- **Consumo de Tokens e Cotas**: Redução expressiva no tamanho dos prompts para o Gemini ao evitar reanálise de repositórios conhecidos do usuário.
