# Design: Remediação da auditoria completa do sistema

## Context

Motivação em `proposal.md`. O estado atual que define a abordagem:

- `history_manager.get_supabase_client()` devolve um singleton criado com a chave **anon**, usado por todas as sessões Streamlit do processo, inclusive para `auth.sign_in_with_password`. O supabase-py (`supabase/_sync/client.py:334`) troca o header `Authorization` do PostgREST para o JWT do último `SIGNED_IN`. O app nunca envia o JWT do usuário de propósito, então o RLS avalia `auth.uid()` de quem logou por último ou `NULL`.
- A sessão sobrevive ao F5 por um token HMAC próprio (`auth_manager.create_session_token`), guardado em localStorage e em cookie não-HttpOnly e também aceito via `?auth_token=`. O segredo tem valor padrão no código.
- `st.context.cookies` reflete apenas a requisição HTTP inicial da página. Ele não muda quando o JS remove o cookie durante a sessão.
- O pipeline (`src/agents/nodes.py`) usa os rótulos `LABELS[lang]` no gerador, mas o revisor usa títulos fixos em português. O executor da UI mescla os updates do `graph.stream` com `dict.update`, o que descarta o reducer `operator.add` de `errors`.
- As 11 changes anteriores estão concluídas, mas não arquivadas. Duas delas (`improve-agent-quality-and-token-efficiency` e `modernize-multi-agent-pipeline`) não arquivam porque os blocos MODIFIED descartam cenários. Os deltas desta change foram escritos contra o estado pós-archive e validados (`--strict`) numa simulação.

## Goals / Non-Goals

**Goals:**
- Fazer do servidor a única fronteira de confiança de dados, com isolamento por `user_id` garantido em um único ponto do código.
- Reduzir o mecanismo de sessão ao mínimo que sobrevive ao F5: um cookie assinado e com expiração.
- Corrigir os bugs do pipeline sem acrescentar nós ao grafo.

**Non-Goals:**
- Login social, OIDC ou `st.login()`.
- Reescrever o histórico do git para apagar os currículos já commitados.
- Cookie HttpOnly: exigiria um servidor HTTP próprio na frente do Streamlit.
- Refresh/rotação de tokens do Supabase: com a service role, o app não usa mais o JWT do usuário para os dados.
- Resolver a divergência pré-existente entre `user-auth` "Modo visitante e uso anônimo" e `auth-access-control` (rotas privadas bloqueadas para visitantes).

## Decisions

### 1. Service role no servidor e cliente anon descartável para autenticação
- **Dados:** um cliente criado com `SUPABASE_SERVICE_ROLE_KEY`, singleton por processo. É seguro compartilhá-lo porque ele nunca chama `auth.*` e, portanto, nunca troca de identidade. Toda query passa por um helper único `_owned(query, user_id)` que aplica `.eq("user_id", user_id)` e rejeita `user_id` vazio ou de convidado. `load_application` e `delete_application` por id também passam por ele.
- **Autenticação:** `sign_in_with_password` e `sign_up` criam um cliente anon novo por chamada, sem auto-refresh (o supabase-py agenda um timer de refresh por sessão), descartado em seguida. Assim nenhuma sessão herda o estado de autenticação de outra. `sign_out` foi removido: como nenhuma sessão do Supabase é guardada, o logout é só local (flag de sessão e cookie expirado).
- **Modo nuvem** só quando `SUPABASE_URL`, `SUPABASE_KEY` e `SUPABASE_SERVICE_ROLE_KEY` estão presentes. Faltando qualquer um, o app inteiro roda em modo local, e a tela Sistema diz qual variável falta.
- **Alternativa descartada:** JWT do usuário por requisição. Exigiria guardar o refresh token no cookie e lidar com a rotação de uso único entre abas. Foi a escolha do usuário na abertura da change.

### 2. Sessão apenas por cookie assinado
- Payload: `{user_id, email, display_name, exp}`, com `exp` em 30 dias, igual ao `max-age` atual. O `access_token` sai do payload.
- `AUTH_SECRET_KEY` é obrigatório. `auth_manager` levanta `RuntimeError` sem ele, e `app.py` mostra `st.error` com instrução e chama `st.stop()` antes de renderizar qualquer página.
- Saem a leitura de `?auth_token=`, o uso de localStorage e o "reload" injetado no documento pai. O cookie (`SameSite=Strict`, mais `Secure` sob HTTPS) já viaja no F5 e é lido por `st.context.cookies`. O componente de sincronização passa a só gravar ou expirar o cookie, o que corta cerca de 60 linhas de JS.
- **Alternativa descartada:** manter localStorage como fonte primária. Ele só existia para alimentar o cookie, e era daí que vinha o ciclo de reload.

### 3. Logout persistente na sessão Streamlit
O `st.session_state["logged_out"] = True` deixa de ser removido no rerun seguinte. A restauração por cookie é pulada enquanto a flag existir, e só um login bem-sucedido a remove (o que `auth_views` já faz). Isso basta porque a flag vive exatamente o mesmo tempo que o snapshot obsoleto de `st.context.cookies`: um novo carregamento de página cria sessão nova, sem a flag, e com o cookie já expirado. O parâmetro `?action=logout` deixa de ser necessário.

### 4. Login local por e-mail
Sem Supabase, `user_id = "local-" + sha256(email.lower())[:16]`. Isso isola o histórico e o perfil por conta local sem armazenar senha. As telas de login e cadastro exibem `st.warning` de modo de desenvolvimento quando `is_supabase_configured()` é falso.

### 5. Executor único do pipeline e avisos persistidos
- Uma função `run_pipeline(graph, inputs, on_node)` em `src/ui/wizard_view.py`, usada também pela re-otimização, consome `graph.stream(..., stream_mode=["updates", "values"])`. Os eventos `updates` alimentam o checklist e a prévia; o último `values` é o estado final, com o reducer de `errors` aplicado.
- Um construtor único do estado inicial substitui as duas cópias de `GraphState(...)`.
- Os avisos não fatais são gravados em `diagnostic["run_warnings"]` e exibidos por `render_ats_diagnostic_panel`. Assim aparecem também quando a candidatura é reaberta, e a chave de sessão `run_errors_*` sai.

### 6. Remoção do tool-calling `get_repo_deep_dive`
O gerador passa a usar sempre `_portfolio_context(state, 1200)`, até 3 READMEs higienizados (cerca de 900 tokens), numa única chamada. Saem `make_repo_deep_dive_tool`, a tool morta no nível do módulo, o import de `MagicMock`, `ToolMessage` e `tool`, e o caminho de fallback duplicado.
- **Alternativa descartada:** manter a tool. A segunda chamada reenvia system, currículo e vaga inteiros e custa mais tokens e latência do que os READMEs que ela evitaria.

### 7. Revisão: títulos localizados e modo econômico que corrige o crítico
- A seção alvo dos problemas determinísticos sai de `LABELS[lang]`: URL de repositório fora do portfólio vai para `projects`. Para marcadores `<...>`, a seção é o último cabeçalho `## ` antes da primeira ocorrência; se estiver no cabeçalho do currículo, antes de qualquer `##`, a seção é tratada como não identificável. O ramo inalcançável `"tabela"` sai.
- **Modo econômico:** se houver problema crítico com seção identificável e `review_attempts < MAX_REVIEW_ATTEMPTS`, o revisor determinístico devolve `severity="minor"` com `patch_section`. O roteador existente leva ao `section_patcher` e o limite de tentativas encerra o ciclo. Sem seção identificável, o currículo é aprovado com o problema registrado no diagnóstico.
- O bloco `attempts >= MAX_REVIEW_ATTEMPTS` no topo de `quality_reviewer` sai, porque `route_after_review` já encerra antes.

### 8. Limites de tempo das chamadas de modelo
`timeout=120` e `max_retries=1` nos clientes Gemini e Groq de `_llm()`. O pior caso cai de cerca de 45 min para cerca de 12 min (3 modelos × 2 tentativas × 120 s).

### 9. Cache de repositórios do perfil efetivamente usado
- O botão "Atualizar projetos" chama `github_fetcher` e guarda os repositórios brutos reduzidos aos campos que o ranker usa: `name`, `description`, `language`, `topics`, `stargazers_count`, `fork`, `updated_at`, `html_url`, `default_branch`.
- O Otimizador injeta `raw_github_repos` no estado inicial quando o usuário do GitHub informado é igual ao do perfil e o cache não está vazio. Nesse caso, `github_fetcher` devolve o valor recebido sem chamar a API.
- Entradas antigas do cache sem `html_url` são ignoradas, o que força uma busca normal.
- `github_researcher` sai, porque seu único uso era o perfil.

### 10. Datas e identidade de candidaturas
- `_parse_datetime_naive` passa a usar `datetime.fromisoformat` (Python 3.13 aceita `Z` e offsets). Quando há fuso, converte com `.astimezone()` para o fuso local antes de remover o tzinfo.
- Em edições, `save_resume` preserva o `date` do arquivo existente.
- Com `filepath="supabase:<id>"`, regrava a cópia local que tem o mesmo `supabase_id` em vez de criar outra.

### 11. Detecção de falha de nuvem sem mudar assinaturas
`save_resume` continua devolvendo um caminho. A UI considera falha de sincronização quando `is_supabase_configured()` é verdadeiro e o caminho devolvido não começa com `supabase:`. Isso evita mudar o retorno usado em quatro lugares.

### 12. Schema e RLS
- Políticas `TO authenticated USING/WITH CHECK (auth.uid() = user_id)` nas duas tabelas, e nenhuma política para `anon`, o que nega tudo. A service role ignora o RLS.
- `user_id` obrigatório via `CHECK (user_id IS NOT NULL) NOT VALID`: vale para gravações novas sem falhar por linhas antigas nulas.
- `handle_new_user()` ganha `SET search_path = ''`.

### 13. Score ATS linear
`ats_score = round(base_score * 100)`, limitado a 0..100, sem o piso de 50 nem o teto de 98. Atende ao requisito existente "sem gerar pontuações arbitrárias" de `ats-optimization`, por isso não há delta para essa capability. A mistura de 60% determinístico e 40% LLM no modo estrito continua igual.

### 14. Grafo compilado uma vez por processo
`@st.cache_resource def get_graph(): return build_graph()` em `app.py`.

## Risks / Trade-offs

- [Uma query com a service role sem filtro de `user_id` vaza dados de todos os usuários] → Toda query passa por `_owned()`. Um teste com cliente falso registra as chamadas e falha se alguma operação em `applications` ou `user_profiles` não aplicar `.eq("user_id", ...)`.
- [`SUPABASE_SERVICE_ROLE_KEY` vazada dá acesso total ao banco] → A chave fica só no servidor (`.env`/secrets), nunca vai ao navegador, e é documentada como segredo no README e no `.env.example`.
- [O cookie de sessão é legível por JS, logo exposto a XSS] → `exp` de 30 dias, nenhum token do provedor no payload, `SameSite=Strict` e a sanitização HTML já existente no formatter.
- [Todas as sessões atuais são invalidadas] → Esperado (novo segredo e novo payload); basta um novo login.
- [Linhas antigas do Supabase com `user_id` nulo e arquivos locais sem `user_id`, incluindo os 5 de `history/`, deixam de aparecer] → Documentar no README como recuperá-los: adicionar `"user_id"` ao cabeçalho JSON do arquivo ou fazer `UPDATE ... SET user_id = ...` no SQL Editor.
- [Remover o tool-calling tira uma demonstração "agêntica" do projeto acadêmico] → O grafo mantém fan-out concorrente, ranker determinístico, ciclo de revisão e patch cirúrgico. A tool pode voltar quando o portfólio tiver mais repositórios do que cabe no prompt.
- [Scores ATS novos ficam abaixo dos antigos para currículos de baixa cobertura] → Diagnósticos já salvos mantêm o valor original; só novas execuções usam a escala linear.
- [O conserto dos deltas das duas changes antigas altera artefatos já concluídos] → A alteração só copia cenários existentes que elas descartavam; nenhum texto de requisito muda.

## Migration Plan

1. Consertar e arquivar as 11 changes concluídas, em ordem cronológica (tarefa 1).
2. Gerar o `AUTH_SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`) e copiar a service role key do painel do Supabase para o `.env` ou os secrets do deploy.
3. Reexecutar `supabase_schema.sql` no SQL Editor.
4. Subir o código. Os usuários fazem login de novo.
5. **Rollback:** reverter o commit e reexecutar a versão anterior do `supabase_schema.sql` (disponível no git). A service role key pode ficar configurada sem efeito.

## Open Questions

- A divergência entre `user-auth` "Modo visitante e uso anônimo" (permite otimizar sem conta) e o comportamento atual (rotas privadas bloqueadas para visitantes) fica para uma change própria. Não afeta esta.
