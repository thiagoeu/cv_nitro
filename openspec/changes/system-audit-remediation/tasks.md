# Tasks

## 1. Pré-requisitos OpenSpec

- [x] 1.1 Copiar para os blocos MODIFIED de `improve-agent-quality-and-token-efficiency/specs/resume-optimization/spec.md` os cenários que eles descartam ("Buscar evidências no GitHub": "Usuário com formato inválido" e "Timeout ou instabilidade na API externa"; "Revisar currículo gerado": "Falha de API durante a auditoria"). Fazer o mesmo em `modernize-multi-agent-pipeline` com todos os cenários vigentes dos dois requisitos. Sem mudar nenhum texto de requisito. Verificar com `openspec validate <change>` em cada uma.
- [x] 1.2 Arquivar as 11 changes nesta ordem: `dashboard-cv-upload-coverletter`, `standardized-resume-layout`, `app-hardening-and-quality`, `fix-llm-pipeline-translation-formatting`, `user-auth-and-profile-reuse`, `app-redesign-diagnostics-and-persistence`, `modern-navbar-and-modular-ui`, `guest-landing-and-route-protection`, `global-footer-and-landing-cleanup`, `improve-agent-quality-and-token-efficiency`, `modernize-multi-agent-pipeline`. Verificar que `openspec list` mostra só `system-audit-remediation` e que `openspec validate system-audit-remediation --strict` passa.
- [x] 1.3 Preencher `context:` em `openspec/config.yaml`: artefatos em PT-BR; stack Streamlit + LangGraph + Supabase; Python 3.13; testes pytest sem rede, com Supabase e LLM mockados. Verificar que `openspec instructions proposal --change system-audit-remediation --json` retorna o context.

## 2. Sessão e autenticação

- [x] 2.1 Ler `AUTH_SECRET_KEY` e `SUPABASE_SERVICE_ROLE_KEY` em `src/core/config.py`, remover o segredo padrão de `auth_manager.py` e fazer `app.py` exibir `st.error` com a instrução de geração e chamar `st.stop()` quando o segredo faltar. Adicionar as duas variáveis ao `.env.example` e ao README. Verificar com um teste em `tests/test_auth_manager.py` que gerar ou validar token sem segredo levanta `RuntimeError`, e o `conftest.py` define um segredo de teste.
- [x] 2.2 Mudar o payload do token para `{user_id, email, display_name, exp}` (30 dias, sem `access_token`) e fazer `restore_session_from_token` rejeitar tokens expirados ou adulterados. Verificar com testes de token válido, expirado, assinatura adulterada e ausência de `access_token` no payload decodificado.
- [x] 2.3 Remover de `app.py` a restauração por `?auth_token=`, que passa a vir só de `st.context.cookies`. Verificar com teste (AppTest ou chamada da rotina de restauração) que um token válido na URL deixa o usuário como visitante.
- [ ] 2.4 Reduzir `render_storage_sync` a gravar o cookie no login e expirá-lo no logout (`SameSite=Strict`, `Secure` sob HTTPS), sem localStorage e sem reload injetado. Verificar manualmente que o F5 mantém a sessão e que o cookie some após Sair (DevTools > Application > Cookies).
- [x] 2.5 Manter `st.session_state["logged_out"]` até um novo login e pular a restauração por cookie enquanto a flag existir; remover o uso de `?action=logout`. Verificar com o roteiro manual (F5 com sessão ativa, Sair, clicar em "Entrar"; o usuário continua visitante) ou com o teste `test_app_logout_not_undone_by_stale_cookie`, que reproduz o mesmo cenário.
- [x] 2.6 Fazer `sign_in_with_password` e `sign_up` usarem um cliente anon novo por chamada, sem auto-refresh e sem tocar o cliente de dados; remover `sign_out`, pois nenhuma sessão do Supabase é mantida. Verificar com teste que monkeypatcha `create_client` e confirma uma criação por chamada, e que o cliente de dados nunca recebe chamadas `auth.*`.
- [x] 2.7 No modo local, derivar `user_id = "local-" + sha256(email.lower())[:16]` e exibir `st.warning` de modo de desenvolvimento nas telas de login e cadastro. Verificar com teste em que dois e-mails geram `user_id` distintos e o mesmo e-mail gera o mesmo id, e visualmente pelo aviso.

## 3. Persistência e isolamento de dados

- [x] 3.1 Separar o cliente de dados (service role, singleton) e exigir `SUPABASE_URL`, `SUPABASE_KEY` e `SUPABASE_SERVICE_ROLE_KEY` em `is_supabase_configured()`; a tela Sistema passa a indicar qual variável falta. Verificar com teste de `is_supabase_configured()` para cada combinação faltante.
- [x] 3.2 Criar o helper `_owned(query, user_id)` e aplicá-lo em todas as operações de `applications` (`list`, `load`, `save`/`update`, `delete`) e de `user_profiles`, recusando `user_id` vazio ou `guest_local`. Verificar com teste usando cliente falso que registra a cadeia de chamadas: toda operação contém `.eq("user_id", <dono>)`, e carregar ou excluir o id de outro usuário retorna vazio ou `False`.
- [x] 3.3 Em `list_resumes`, selecionar só `id,user_id,job_title,job_url,language,technologies,created_at,has_cover_letter,diagnostic`, unificar o mapeamento de linha em uma função e remover o ramo `user_id is None`, ajustando `tests/test_history.py` e `tests/test_end_to_end_flow.py`. Verificar pelo teste que confere a string do `select` e pela suíte de histórico verde.
- [x] 3.4 Listar na pasta local apenas os arquivos cujo `user_id` é igual ao do usuário atual. Verificar com teste em que arquivos sem `user_id` e de outro usuário não aparecem.
- [x] 3.5 Converter datas com fuso para o horário local em `_parse_datetime_naive` e preservar `date` em edições de candidatura. Verificar com teste em que `2026-10-25T11:03:06+00:00` exibe a mesma hora local que `datetime.fromisoformat(...).astimezone()`, e com teste em que editar não altera `date` nem a ordem da lista.
- [x] 3.6 Para `filepath="supabase:<id>"`, regravar a cópia local com o mesmo `supabase_id` em vez de criar arquivo novo. Verificar com teste em que três saves seguidos deixam um único arquivo local.
- [x] 3.7 Exibir aviso "não sincronizado com a nuvem" no Otimizador, na re-otimização e nos três editores quando o Supabase está configurado e `save_resume` devolve caminho local. Verificar com teste em que um cliente falso falha no `insert`: o arquivo é salvo e o aviso aparece.
- [x] 3.8 Mudar a assinatura para `sync_local_to_supabase(user_id)`: enviar apenas os arquivos daquele `user_id`, com `user_id` no payload; a tela Sistema passa o usuário atual. Verificar com teste em que, numa pasta com arquivos de A e B, só os de A são enviados, todos com `user_id` de A.
- [x] 3.9 Remover `clean_test_records_from_supabase` e o botão "Limpar registros de teste". Verificar que `grep -r clean_test_records src app.py` não retorna nada.
- [ ] 3.10 Reescrever as políticas em `supabase_schema.sql` (`TO authenticated` com `auth.uid() = user_id`, nenhuma para `anon`), adicionar `CHECK (user_id IS NOT NULL) NOT VALID` nas duas tabelas e `SET search_path = ''` em `handle_new_user()`. Atualizar o texto do expander da tela Sistema e o README com o passo de migração e a recuperação de registros sem dono. Verificar no SQL Editor que o script roda sem erro e que uma consulta REST com a chave anon a `applications` e `user_profiles` retorna 0 linhas.
- [x] 3.11 Trocar `.history/` por `history/*` com `!history/.gitkeep` no `.gitignore` e rodar `git rm -r --cached` nos 5 arquivos de `history/`, sem commit. Verificar com `git status`: remoções no índice e arquivos ainda presentes no disco.

## 4. Pipeline multi-agente

- [ ] 4.1 Remover o tool-calling: `resume_generator` usa sempre `_portfolio_context(state, 1200)` numa única chamada. Apagar `make_repo_deep_dive_tool`, a tool do módulo, `MagicMock`, `ToolMessage` e `tool`, e atualizar `tests/test_nodes.py`. Verificar que `grep -rn "MagicMock\|deep_dive" src` não retorna nada e que um teste confirma exatamente um `invoke` do LLM no gerador.
- [ ] 4.2 Configurar `timeout=120` e `max_retries=1` nos clientes Gemini e Groq de `_llm()`. Verificar com teste que inspeciona os kwargs dos construtores mockados.
- [ ] 4.3 Derivar a seção alvo dos problemas determinísticos de `LABELS[lang]` (URL de repositório leva a `projects`; marcador leva ao último `## ` antes dele) e remover o ramo inalcançável `"tabela"`. Verificar com teste em que um currículo EN com URL fora do portfólio produz `patch_section == "KEY PROJECTS"` e `splice_markdown_section` altera a seção.
- [ ] 4.4 No modo econômico, devolver `severity="minor"` com `patch_section` quando houver problema crítico com seção identificável e `review_attempts < MAX_REVIEW_ATTEMPTS`; caso contrário, aprovar e registrar no diagnóstico. Verificar com teste do grafo com LLM mockado (modo econômico com URL falsa): o `section_patcher` roda uma vez e o revisor LLM não é chamado.
- [ ] 4.5 Remover o bloco `attempts >= MAX_REVIEW_ATTEMPTS` do topo de `quality_reviewer`. Verificar que `tests/test_agents.py` e `tests/test_agent_quality_improvements.py` continuam verdes.
- [ ] 4.6 Trocar o score ATS determinístico para `round(base_score * 100)`, limitado a 0..100, ajustando os testes de faixa. Verificar com teste em que nenhum termo coincidente dá score < 50 e cobertura total dá 100.
- [ ] 4.7 Cache de repositórios do perfil:
  - "Atualizar projetos" passa a gravar a saída de `github_fetcher` reduzida aos campos do ranker;
  - o Otimizador injeta `raw_github_repos` quando o usuário do GitHub é igual ao do perfil;
  - `github_fetcher` devolve o valor recebido sem chamar a API;
  - entradas sem `html_url` são ignoradas;
  - `github_researcher` sai;
  - a dica da tela Sistema é corrigida.

  Verificar com teste em que `github_fetcher` não chama `requests.get` quando recebe `raw_github_repos`, e manualmente na aba de rede.
- [ ] 4.8 Extrair `_github_headers()`, remover o header `mercy-preview` e usar `per_page=100`. Verificar com os testes de GitHub existentes verdes e um teste da URL montada.

## 5. Interface e execução

- [x] 5.1 Criar `run_pipeline(graph, inputs, on_node)` com `stream_mode=["updates", "values"]` e um construtor único do estado inicial, usados pelo Otimizador e pela re-otimização. Verificar com teste em que um grafo com dois nós que emitem `errors` produz um estado final com os dois erros.
- [x] 5.2 Gravar `final_state["errors"]` em `diagnostic["run_warnings"]`, exibir no painel de diagnóstico e remover a chave `run_errors_*`. Verificar com teste do painel com `run_warnings` e visualmente reabrindo a candidatura.
- [ ] 5.3 Compilar o grafo uma vez com `@st.cache_resource` em `app.py`. Verificar com teste que monkeypatcha `build_graph` e confirma uma única chamada em dois reruns (AppTest).
- [ ] 5.4 Contar tecnologias no dashboard sem diferenciar maiúsculas, exibindo a grafia mais frequente. Verificar com teste em que `["AWS", "aws", "TypeScript"]` resulta em `AWS: 2` e `TypeScript: 1`.
- [x] 5.5 Unificar as três chamadas de salvamento dos editores em `applications_view.py` num helper local que repassa os metadados da candidatura. Verificar com `tests/test_app_views.py` verde.
- [ ] 5.6 Trocar `use_container_width=True` por `width="stretch"` em `landing_view.py`. Verificar que nenhum aviso de depreciação aparece ao abrir a landing.

## 6. Limpeza e dependências

- [ ] 6.1 Remover os wrappers `render_dashboard`, `render_settings` e `render_applications_list` de `app.py`, os aliases `MAIN_LINKS`/`ACCOUNT_LINKS` e `get_current_page` de `navbar.py`, e `load_resume`/`load_cover_letter` de `history_manager.py`, migrando os testes para as funções reais. Verificar por grep sem referências restantes e suíte verde.
- [ ] 6.2 Remover `tests/test_env.py`, que não contém testes. Verificar que `pytest --collect-only` não lista o arquivo.
- [ ] 6.3 Em `requirements.txt`, remover `langchain`, `google-generativeai`, `google-genai` e `tabulate`, adicionar `langchain-core` e `pydantic` (importados diretamente) e definir versões mínimas iguais às instaladas. Verificar com instalação num venv limpo seguida de `pytest`.
- [ ] 6.4 Atualizar o README com o fluxo do gerador sem tool-calling, o modo local de desenvolvimento e a nova escala do score ATS. Verificar que as seções citam os comportamentos atuais e não mencionam `get_repo_deep_dive`.

## 7. Verificação integrada

- [ ] 7.1 Rodar a suíte completa (`pytest -q`). Verificar que tudo passa sem acesso à rede.
- [ ] 7.2 Em dois navegadores, logar usuários A e B no mesmo servidor, salvar uma candidatura em cada um e fazer logout de B. Verificar no painel do Supabase as duas linhas com os `user_id` corretos e que A continua salvando após o logout de B.
- [ ] 7.3 Executar uma otimização para vaga em inglês com usuário do GitHub inexistente e carta ativada no modo econômico. Verificar que a candidatura abre com o aviso do GitHub no diagnóstico, as datas aparecem no fuso local e o currículo está em inglês.

## Workflow follow-up

- O commit das alterações fica a cargo do usuário; nenhuma tarefa desta change faz commit.
- Arquivar `system-audit-remediation` depois da revisão e confirmar com `openspec list --specs` que `user-auth`, `resume-history` e `resume-optimization` refletem os deltas.
