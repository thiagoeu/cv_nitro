# Proposal: Remediação da auditoria completa do sistema

## Why

A auditoria de 01/11/2026 encontrou falhas que expõem dados pessoais (currículos base, e-mails, histórico de vagas) e quebram a persistência em nuvem:
- sessões forjáveis: o segredo HMAC tem valor padrão versionado e o token nunca expira;
- RLS que libera a leitura de todos os perfis para a chave anon pública;
- cliente Supabase global que herda o JWT do último usuário logado, fazendo gravações caírem em silêncio no fallback local;
- logout desfeito na interação seguinte.

Somam-se bugs no pipeline multi-agente, como o patch de seção que não faz nada em vagas EN/ES, erros não fatais que nunca chegam ao usuário e o modo econômico aprovando currículo com URL de repositório inventada. Isso precisa ser corrigido antes de qualquer deploy público.

## What Changes

**Segurança e autenticação**
- **BREAKING** `AUTH_SECRET_KEY` passa a ser obrigatório: o app não inicia sem ele. O token de sessão ganha expiração (`exp`), deixa de carregar o `access_token` do Supabase e não é mais aceito via `?auth_token=` na URL. Todas as sessões atuais são invalidadas.
- **BREAKING** O backend passa a acessar os dados com `SUPABASE_SERVICE_ROLE_KEY` (só no servidor) e filtra por `user_id` em toda leitura, gravação e exclusão. Login e cadastro usam um cliente anon descartável por chamada, para que nenhuma sessão herde o estado de autenticação de outra.
- **BREAKING** Novo script de RLS: `anon` sem acesso a `applications` e `user_profiles`, `authenticated` restrito às próprias linhas e `user_id NOT NULL`. A função do trigger ganha `search_path` fixo.
- O logout continua valendo até a página ser recarregada; o cookie antigo não restaura mais a sessão.
- O login local (sem Supabase) gera um `user_id` por e-mail, em vez do compartilhado `local_dev_user`, e a interface sinaliza que é modo de desenvolvimento sem verificação de senha.
- Saem do sistema o botão "Limpar registros de teste" e `clean_test_records_from_supabase`.
- `history/` sai do versionamento; arquivos sem dono deixam de aparecer para usuários autenticados.

**Histórico e persistência**
- Falha ao gravar no Supabase gera aviso visível em vez de fallback silencioso.
- A sincronização do histórico local envia só os arquivos do usuário atual e já com o `user_id` dele.
- As datas são exibidas no fuso local, tanto para registros do Supabase quanto locais.
- A edição preserva a data de criação e não cria arquivos locais duplicados.
- A listagem busca só as colunas leves, sem currículo, vaga e currículo base de cada linha.

**Pipeline multi-agente**
- O patch de seção usa os títulos no idioma da vaga.
- O modo econômico corrige defeitos críticos determinísticos com um patch de seção, sem acionar o revisor LLM.
- Os avisos não fatais de todos os nós são acumulados e exibidos na tela da candidatura.
- Sai o tool-calling `get_repo_deep_dive`: os READMEs higienizados dos top-3 repositórios vão direto no prompt do gerador. Isso também remove o import de `MagicMock` do código de produção.
- As chamadas de modelo passam a ter timeout de 120 s e 1 retry por modelo; a cadeia de fallbacks cuida do resto.
- O score ATS perde o piso artificial de 50 e passa a ser linear de 0 a 100.
- O cache de repositórios do Perfil passa a ser usado pelo pipeline, cumprindo o requisito já existente em `user-profile-reuse`.
- A re-otimização usa o mesmo executor com streaming do Otimizador.

**Performance e limpeza**
- O grafo é compilado uma vez por processo (`st.cache_resource`).
- Saem: os wrappers e aliases que só existiam para os testes, o ramo inalcançável do revisor, a tool morta, dependências não importadas e a API depreciada `use_container_width`.
- O contador de tecnologias do dashboard para de quebrar maiúsculas ("AWS", "TypeScript").

**Processo (OpenSpec)**
- As 11 changes concluídas são arquivadas antes desta, já que os deltas abaixo modificam requisitos que hoje só existem nelas.
- O `openspec/config.yaml` ganha `context`.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `user-auth`: token de sessão com segredo obrigatório e expiração; logout persistente; autenticação local isolada por e-mail; isolamento de dados no servidor com RLS fechado para anon.
- `resume-history`: persistência com dono obrigatório e falha de nuvem visível; listagem restrita ao dono, com datas no fuso local; edição que preserva identidade e data.
- `resume-optimization`: evidências do GitHub injetadas no prompt (sem tool-calling); revisão com patch localizado e modo econômico que corrige defeitos críticos; avisos não fatais visíveis; tempo máximo por chamada de modelo.

## Impact

- **Código:** `app.py`, `src/core/auth_manager.py`, `src/core/history_manager.py`, `src/core/profile_manager.py`, `src/core/config.py`, `src/agents/nodes.py`, `src/agents/graph.py`, `src/ui/wizard_view.py`, `src/ui/applications_view.py`, `src/ui/settings_view.py`, `src/ui/profile_view.py`, `src/ui/dashboard_view.py`, `src/ui/landing_view.py`, `src/ui/navbar.py`, `supabase_schema.sql`, `tests/*`.
- **Configuração:** novas variáveis `AUTH_SECRET_KEY` (obrigatória) e `SUPABASE_SERVICE_ROLE_KEY` (obrigatória quando o Supabase estiver ativo) no `.env` e no `.env.example`.
- **Banco:** é preciso reexecutar `supabase_schema.sql` no SQL Editor. Linhas antigas com `user_id` nulo ficam inacessíveis pelo app.
- **Usuários:** todas as sessões salvas no navegador são invalidadas (novo login necessário).
- **Dependências:** saem `langchain`, `google-generativeai`, `google-genai` (transitiva) e `tabulate`; entram versões mínimas.
- **Fora de escopo:** reescrever o histórico do git para apagar os currículos já commitados em `history/`. Tirá-los do índice não os remove dos commits antigos.
