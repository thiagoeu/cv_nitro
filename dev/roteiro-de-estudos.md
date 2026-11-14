# Caderno e Roteiro de Estudos

Material de revisao continua de conceitos tecnicos, boas praticas de engenharia e operacao de repositorios.

---

## 1. Autoria no Git e Mecanismo de Contribuidores no GitHub

### O que e o trailer `Co-Authored-By`?
No Git, e possivel atribuir co-autoria a um commit adicionando uma linha especifica no final da mensagem do commit, conhecida como trailer de metadados:

```text
refactor(auth): ajusta validacao de tokens JWT

Co-Authored-By: Nome <email@dominio.com>
```

### Como o GitHub interpreta esse trailer?
1. **Deteccao automatica**: O GitHub le o rodape da mensagem do commit. Caso encontre a sintaxe `Co-Authored-By: Nome <email>`, ele busca a conta vinculada aquele e-mail.
2. **Lista de Contribuidores (Contributors)**: O autor do e-mail e automaticamente adicionado a secao oficial de "Contributors" na barra lateral direita do repositorio.
3. **Avatares duplos**: Na listagem de commits do GitHub, passam a aparecer dois avatares lado a lado (o autor original e o co-autor).

### Por que o Claude apareceu como contribuidor em commits antigos?
Ferramentas de assistencia via terminal (como o Claude Code da Anthropic) possuem configuracao padrao de injetar a linha `Co-Authored-By: Claude <noreply@anthropic.com>` automaticamente em qualquer commit gerado pela ferramenta. Nao se tratou de uma escolha manual de portfólio, mas sim de um comportamento automatizado da ferramenta de IA ao commitar.

### Impacto no Portfólio (Fica ruim/feio?)
**Sim, em geral e prejudicial para portfólios de avaliacao tecnica e recrutamento:**
- **Percepcao de dependencia**: Recrutadores e gestores tecnicos podem interpretar que o projeto nao foi desenvolvido pelo candidato, gerando duvidas sobre o real dominio dos conceitos e da arquitetura.
- **Divisao de autoria**: A secao "Contributors", que deveria destacar exclusivamente voce como unico criador e mantenedor do projeto, divide espaco com uma conta de bot/IA.
- **Deteccao visual rapida**: Na timeline do GitHub, os commits com avatar de bot chamam atencao negativa imediata em uma triagem tecnica.

### Boas Praticas e Como Prevenir
1. **Controle manual de commits**: Sempre revisar as mensagens de commit antes de executa-las, evitando que ferramentas adicionem linhas de rodape indesejadas.
2. **Remocao de trailers**: Caso uma IA prepare o texto do commit, remover qualquer linha iniciada por `Co-Authored-By:`.
3. **Padrao de mensagens**: Manter mensagens no padrao Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`) puramente tecnicas, sem creditos de assistentes de IA.

---

## 2. Resiliencia de Widgets Dinamicos em Perfis do GitHub

### Por que os cards de estatisticas quebram?
Servicos como `github-readme-stats.vercel.app` e geradores de streak publicos operam em modelos serverless (Vercel, Heroku, etc.) e sofrem com:
1. **Pausa de Deploy por Limite de Trafego (HTTP 503 / DEPLOYMENT_PAUSED)**: Instancias publicas gratuitas esgotam a cota global de bandwidth fornecida pela Vercel e entram em suspensao automatica.
2. **Rate Limit da API do GitHub**: Instancias compartilhadas excedem o teto de requisicoes por hora da API REST do GitHub caso nao utilizem tokens rotativos (PATs).
3. **Descontinuacao de Dominios (HTTP 402 / DEPLOYMENT_DISABLED)**: Dominios mantidos por criadores independentes (ex: `nirzak-streak-stats.vercel.app`) sao desativados quando planos expiram.

### Estrategias de Mitigacao
- **Migracao para Forks Ativos (Drop-in)**: Adotar mirrors oficiais mantidos pela comunidade, como `github-stats-extended.vercel.app` para estatisticas gerais e `streak-stats.demolab.com` para monitoramento de streak.
- **Deploy Proprio (Self-Hosted)**: Criar um fork do projeto em sua propria conta Vercel/Railway com um token PAT pessoal, garantindo isolamento total de cota.
- **Geracao via GitHub Actions (Zero Dependencia Externa)**: Executar uma Action agendada (cron diario) que consulta as metricas locais, compila o SVG estatico e comita diretamente na branch do perfil.

---

## 3. Reescrita de Historico Git para Remocao de Metadados de Co-Autoria

### Como o Git calcula o hash de um commit?
O identificador SHA de um commit e gerado a partir de uma arvore criptografica que inclui:
- A arvore de arquivos e diretorios (tree hash).
- Os hashes dos commits pais (parent hashes).
- O nome e e-mail do autor e do committer com seus respectivos timestamps.
- A **mensagem do commit** em sua totalidade.

Ao alterar ou remover qualquer linha da mensagem (como `Co-Authored-By:`), o hash daquele commit muda obrigatoriamente. Consequentemente, todos os commits posteriores passam a ter um novo hash, gerando a divergencia de historico entre o repositorio local e o remoto (`origin/main`).

### Fluxo Seguro de Reescrita de Historico
1. **Criacao de branch de seguranca**: Antes de qualquer reescrita, criar uma referencia exata do estado atual (`git branch backup-main main`).
2. **Filtragem das mensagens**: Aplicar filtro apenas no corpo das mensagens com ferramenta nativa (`git filter-branch --msg-filter "sed '/[Cc]o-[Aa]uthored-[Bb]y/d'"`) ou `git-filter-repo`.
3. **Validacao de integridade**: Executar `git diff backup-main..main`. O retorno deve ser rigorosamente vazio, garantindo que nenhuma linha de codigo foi alterada.
4. **Sincronizacao remota**: Enviar o novo historico com `git push origin main --force` para substituir os commits remotos no GitHub e desvincular o co-autor da vitrine do repositorio.

---

## 4. Por que Contribuidores Antigos Ainda Podem Aparecer Apos o Force Push na Main?

Mesmo apos reescrever com sucesso a branch `main`, o GitHub pode continuar listando contas antigas em `/graphs/contributors` por dois motivos essenciais:

1. **Branches Remotas Secundarias com Commits Antigos**:
   - O algoritmo de contribuidores do GitHub varre **todas as branches e tags ativas no repositorio remoto**, nao apenas a branch `main`.
   - Se existirem branches antigas (por exemplo, `fix/multi-agent-audit` ou `fix/system-audit-remediation`) que ainda apontam para commits com o trailer `Co-Authored-By`, esses commits continuam alcancaveis (reachable) pelo Git no servidor.
   - **Solucao**: Excluir branches remotas antigas que ja foram incorporadas a `main` (`git push origin --delete <nome-da-branch>`).

2. **Politica de Cache do Grafo de Contribuidores do GitHub**:
   - A pagina `/graphs/contributors` e gerada de forma assincrona e utiliza cache agressivo em segundo plano.
   - Apos a remocao de todas as referencias que apontam para os commits indesejados, o GitHub agenda um reprocessamento do historico que pode levar de alguns minutos ate 24 horas para atualizar a interface visual web.

---

## 5. Referencias Remotas Obsoletas (Stale Tracking Branches) e Cache de Navegador

### O erro `remote ref does not exist`
Ao tentar deletar uma branch remota com `git push origin --delete <branch>` e receber o erro `remote ref does not exist`, significa que a branch ja foi deletada no GitHub, mas a copia local do Git ainda mantinha o ponteiro de rastreamento salvo em `.git/refs/remotes/origin/`.

### Como sincronizar e podar ponteiros mortos?
Para sincronizar a visao local com as branches reais que ainda existem no servidor:
```bash
git remote prune origin
# ou alternativamente:
git fetch -p
```
Esse comando faz a poda (pruning) imediata de qualquer referencia que nao exista mais no repositorio remoto.

### Cache de Navegador na Pagina de Contribuidores
Mesmo apos o GitHub processar a remocao e a API retornar apenas o autor legitimo, a aba aberta no navegador ou o cache local de HTTP pode continuar exibindo a versao antiga. Para forcar a exibicao da versao atualizada:
- No Windows/Linux: `Ctrl + F5` ou `Shift + F5`
- No macOS: `Cmd + Shift + R`
- Ou abrir o link em uma janela anonima.

---

## 6. Estrategias de Cache, Invalidacao e Sincronizacao em Integracoes com APIs Externas

### O Dilema: Latencia e Consumo de Tokens vs. Dados Frescos (Staleness)
Em aplicacoes que integram pipelines de agentes inteligentes com fontes externas (como a API do GitHub), o cache de dados e crucial para:
1. **Evitar latencia de rede**: Buscar dezenas de repositorios e seus respectivos READMEs a cada execucao atrasa o pipeline em varios segundos.
2. **Proteger cotas de taxa (Rate Limits)**: A API publica do GitHub limita chamadas nao autenticadas a 60 requisicoes por hora (ou 5.000 com token).
3. **Economizar tokens de IA**: Evita reprocessar textos que nao sofreram alteracoes.

No entanto, um cache permanente sem regra de expiracao cria o risco de **pontos cegos (stale cache)**: projetos recem-criados de alto valor para uma candidatura especifica deixam de ser capturados pelos agentes.

### Abordagens de Otimizacao e Invalidacao

1. **Sincronizacao Sob Demanda no Ponto de Uso (UI-Driven Invalidation)**:
   - Em vez de exigir que o usuario navegue ate uma aba de configuracoes ou perfil, o proprio formulario de envio (Wizard) exibe o status atual do cache (ex: "18 repositorios em cache") e disponibiliza um botao de acao rapida ("Atualizar projetos do GitHub agora").
   - Vantagem: Zero desperdicio de requisicoes; o usuario decide conscientemente quando acabou de subir um repositorio novo.

2. **Deteccao Leve de Defasagem (Lightweight Metadata Check)**:
   - Antes de iniciar o pipeline, uma chamada simples ao endpoint do usuario (`GET https://api.github.com/users/{username}`) retorna o atributo `public_repos` (custo de apenas 1 requisicao leve).
   - Se `public_repos != len(cached_repos)`, o sistema detecta a criacao ou remocao de projetos e dispara o fetch completo ou exibe alerta imediato na interface.

3. **Time-To-Live (TTL) e Registro de Timestamp**:
   - Registrar no perfil a data/hora da ultima sincronizacao (`github_synced_at`).
   - Definir uma regra temporal de expiracao (por exemplo, 24 horas ou 7 dias) apos a qual o cache e considerado obsoleto e precisa ser renovado.

4. **Requisicoes Condicionais HTTP (ETags / If-None-Match)**:
   - O GitHub fornece cabecalhos `ETag` nas respostas de listagem.
   - Ao reenviar a requisicao com o cabecalho `If-None-Match: <etag>`, caso nao haja mudancas, o servidor responde com HTTP 304 (Not Modified), consumindo quase nada do rate limit e confirmando a validade dos dados locais.

### Boas Praticas de UX em Interfaces Streamlit
Ao implementar botoes de sincronizacao em tempo real em aplicacoes Streamlit, e fundamental vincular os inputs com chaves persistentes (`key` no `st.session_state`). Isso assegura que, ao clicar em "Atualizar projetos", o recarregamento (`st.rerun()`) nao apague o texto da vaga ou o curriculo base que o usuario ja havia colado na tela.

---

## 7. Arquitetura de Skills em Agentes de IA e a Abordagem Ponytail (YAGNI e Engenharia Minimalista)

### Como funcionam as Skills no Antigravity?
No ecossistema do Antigravity, **Skills** sao extensoes de capacidade e comportamento do agente. Elas sao declaradas atraves de pastas contendo arquivos `SKILL.md` (localizadas tanto no diretorio global do usuario `~/.gemini/config/skills/` quanto no workspace local).
- O agente carrega a metadata das skills instaladas em seu contexto.
- Ao identificar gatilhos contextuais (palavras-chave, intencoes ou tarefas de programacao), o agente le as instrucoes detalhadas da skill e adota o comportamento instruido.

### O que e a skill `ponytail`?
A skill `ponytail` implementa o arquetipo do **"Lazy Senior Developer"** (desenvolvedor senior pragmatico). O principio fundamental e: *"o melhor codigo e o codigo que nunca precisou ser escrito"*.
- **Foco no menor diff funcional**: Resolver o problema de ponta a ponta com a menor quantidade de codigo novo possivel.
- **Evitar sobre-engenharia (Over-engineering)**: Nada de abstracoes prematuras, wrappers desnecessarios, configuracoes para "caso precise no futuro" ou introducao de dependencias externas para resolver algo simples.
- **Aderencia ao codigo existente**: Aproveitar utilitarios, bibliotecas padrao e convencoes ja presentes no projeto antes de inventar novas camadas.
- **Lazy na solucao, rigoroso no impacto**: Manter seguranca, validacao em fronteiras de confianca, tratamento de erros e atualizar chamadores e testes afetados.

### Niveis de atuacao do Ponytail
1. **lite**: Constroi estritamente o que foi pedido, sugerindo uma opcao mais simples em uma linha para o usuario decidir.
2. **full (padrao)**: Aplica o menor diff funcional completo, eliminando qualquer codigo superfluo.
3. **ultra**: Questiona a propria necessidade da demanda antes de codificar, desafiando requisitos inflados.

---

## 8. Execucao Headless de Agentes vs. Terminal Integrado Interativo da IDE

### Como o Antigravity executa comandos de shell?
Quando o agente precisa rodar comandos (como testes `pytest`, checagem de arquivos ou comandos do `openspec`), ele utiliza a ferramenta interna `run_command`.
Essa ferramenta dispara os processos em um subprocesso em segundo plano (modo **Headless**), em vez de digitar os comandos na janela do terminal aberta na interface.

### Por que os comandos nao sao digitados no terminal visivel do usuario?
1. **Isolamento de sessao e concorrencia**: Se o agente executasse diretamente no terminal visivel, haveria disputa de foco entre o que o usuario esta digitando e a saida do assistente, podendo corromper comandos do usuario.
2. **Nao bloqueio da interface**: Processos demorados ou em background travariam o prompt interativo do desenvolvedor.
3. **Captura estruturada de saida**: O runtime precisa ler os fluxos de `stdout`, `stderr` e o `exit code` de maneira deterministica para tomar decisoes e reportar falhas.

### Como acompanhar o que esta sendo executado em tempo real?
1. **Caixas de Ferramenta no Chat (Tool Calls)**:
   - Toda execucao gera um card expansivel no chat do Antigravity.
   - Clicando no bloco, e possivel visualizar o comando exato disparado, o tempo de execucao e os logs completos retornados.
2. **Arquivos de Log das Tarefas**:
   - Comandos assincronos gravam a saida diretamente nos arquivos de log da sessao em `.system_generated/tasks/task-<id>.log`.
3. **Execucao Manual no Terminal Integrado**:
   - O usuario pode abrir o terminal integrado da IDE pelo atalho `Ctrl + \`` (ou `Ctrl + J`).
   - Para rodar os mesmos comandos manualmente com o ambiente virtual do projeto:
     ```powershell
     .\venv\Scripts\Activate.ps1
     pytest tests/test_github_cache_invalidation.py -v
     pytest -q
     ```

---

## 9. Migracoes de Banco de Dados e Execucao de DDL no Supabase (PostgreSQL)

### Por que o SDK de aplicacao (supabase-py) nao roda migrations sozinho?
Bibliotecas clientes como `supabase-py` comunicam-se com o Supabase via camada REST PostgREST. Essa camada foi projetada para manipulacao de dados (DML - `SELECT`, `INSERT`, `UPDATE`, `DELETE`) e nao para comandos estruturais de definicao de schema (DDL - `CREATE TABLE`, `ALTER TABLE`, `DROP COLUMN`).

Para executar instrucoes DDL, e necessario conexao direta com o banco (driver nativo PostgreSQL como `psycopg2`/`asyncpg`) ou privilégios administrativos no painel de controle.

### Idempotencia em Scripts de Migracao
Ao evoluir bancos relacionais em producao, scripts de migracao devem ser **idempotentes** (podem ser executados multiplas vezes sem falhar nem duplicar dados):
- Para criacao: `CREATE TABLE IF NOT EXISTS public.user_profiles (...)`
- Para novas colunas: `ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS github_synced_at TIMESTAMPTZ;`
- Para politicas de seguranca (RLS): `DROP POLICY IF EXISTS ...` antes de recriar `CREATE POLICY ...`.

### Como aplicar migracoes no Supabase

1. **Via Painel Web (SQL Editor)**:
   - Indicado para projetos em desenvolvimento e aplicacao direta.
   - Acesso: Painel do Projeto -> Menu lateral esquerdo `SQL Editor` -> `New Query`.
   - Execucao da clausula DDL e confirmacao imediata no schema do Postgres.

2. **Via Supabase CLI**:
   - Indicado para times com pipelines de CI/CD.
   - Criacao de arquivo versionado: `supabase migration new <nome_da_migracao>`
   - Aplicacao remota: `supabase db push`

### Padrao de Resiliencia na Aplicacao (Graceful Fallback)
Mesmo antes de uma migracao ser executada no banco remoto, a camada de acesso a dados (como `profile_manager.py`) deve ser tolerante a falhas:
- Caso o `upsert` com a nova coluna lance uma excecao de coluna inexistente, o codigo intercepta o erro e tenta novamente apenas com as colunas legadas, mantendo o sistema funcional ate que a migracao seja aplicada no banco de dados.

---

## 10. Pausa Automatica por Inatividade no Supabase (Free Tier Pausing) e Operacao Hibrida

### O que significa o projeto estar "Inativo" no Supabase?
Na camada gratuita (Free Tier) do Supabase, projetos que passam 7 dias consecutivos sem receber nenhuma requisicao de API ou conexao com o banco de dados entram automaticamente em estado de **Pausa (Paused / Inativo)**.
- O container do PostgreSQL e suspenso para liberar memoria e processamento nos servidores da nuvem.
- Os dados, esquemas e tabelas permanecem 100% preservados no disco.
- Conexoes externas via API REST (PostgREST) e o SQL Editor web ficam temporariamente inacessiveis ate que o projeto seja despausado.

### Como reativar o projeto
1. Acessar o painel em [supabase.com/dashboard](https://supabase.com/dashboard).
2. Localizar o card do projeto que exibe a etiqueta "Paused" ou "Inativo".
3. Clicar no botao **"Restore project"** (ou "Restaurar projeto").
4. O Supabase leva de 1 a 2 minutos para subir o container do PostgreSQL novamente. Assim que o indicador ficar verde ("Active"), o banco volta a operar normalmente.

### Arquitetura de Armazenamento Hibrido (Resiliencia Offline)
No CV Nitro, a arquitetura foi desenhada para nunca depender criticamente da disponibilidade da nuvem:
- **Fallback transparente**: Se o Supabase estiver inativo, pausado ou sem credenciais no `.env`, a aplicacao chaveia automaticamente para o modo de persistencia local em arquivos (`history/*.md` e `profiles/*.json`).
- **Sincronizacao posterior**: Assim que o banco de dados for reativado, a tela de Sistema permite acionar o botao "Sincronizar historico local" para enviar os dados pendentes para a nuvem.

---

## 11. Modelo de Credenciais do Supabase: Anon Key vs. Service Role Key

### Onde localizar as credenciais no Painel do Supabase
1. No painel do projeto em [supabase.com/dashboard](https://supabase.com/dashboard), acessar a barra lateral esquerda inferior.
2. Clicar no icone de engrenagem (**Project Settings**).
3. Selecionar o menu **API** (ou **Data API** nas versoes recentes).
4. Nessa tela estao localizados a **Project URL** e o bloco **Project API Keys**.

### Anatomia das Credenciais

1. **Project URL (`SUPABASE_URL`)**:
   - E o endereco raiz da sua instancia Supabase na nuvem (formato: `https://<seu-project-id>.supabase.co`).
   - Aponta para os servicos integrados (PostgREST, Auth GoTrue, Storage e Realtime).

2. **Chave Anon / Public (`SUPABASE_KEY`)**:
   - Identificada como `anon` e rotulada como `public`.
   - Pode ser exposta publicamente no frontend (navegador ou app mobile).
   - **Regra de seguranca**: Esta chave e estritamente subordinada as politicas de **Row Level Security (RLS)**. Sem uma politica explicita que autorize a leitura ou gravacao (`USING`/`WITH CHECK`), requisicoes com essa chave retornam lista vazia ou erro 401/403.
   - No CV Nitro: Utilizada exclusivamente para fluxos de autenticacao de usuarios (cadastro e login no Supabase Auth).

3. **Chave Service Role / Secret (`SUPABASE_SERVICE_ROLE_KEY`)**:
   - Identificada como `service_role` e rotulada como `secret`.
   - E a chave de superusuario do banco (ignora completamente todas as politicas RLS - **Bypass RLS**).
   - **Regra de seguranca**: NUNCA deve ser commitada no Git, exposta em codigo-fonte cliente ou enviada para o navegador. Deve residir apenas no ambiente de servidor seguro (`.env`).
   - No CV Nitro: Utilizada no backend para realizar operacoes de sincronizacao de historico, criacao de perfis e manutencao de cotas com isolamento por `user_id` controlado pela aplicacao.

### Transicao de Chaves no Supabase (Novas vs. Legacy API Keys)
Recentemente, o Supabase introduziu um novo padrao de chaves opacas (`sb_publishable_...` e `sb_secret_...`) para substituir progressivamente os tokens JWT legados ate 2027.
- **Novas chaves**: Permitem revogacao granular e rotacao sem alterar o segredo global de JWT do projeto.
- **Botao 'View legacy API keys'**: O painel disponibiliza um botao para visualizar as chaves antigas (`anon` e `service_role` comecadas em `eyJ...`), garantindo compatibilidade retroativa imediata com versoes de SDKs e bibliotecas clientes que validam o formato JWT.
- **Onde encontrar a URL do Projeto nas novas interfaces**: Alem da tela de configuracoes, o botao "Connect" (no topo ao lado da branch) e a secao lateral "Data API" exibem a `Project URL` pronta para copia.











