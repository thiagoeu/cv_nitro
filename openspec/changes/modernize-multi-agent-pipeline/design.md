# Design

## Context

O pipeline atual do CV Nitro executa de forma sequencial síncrona através de `graph.invoke()` no Streamlit. Embora já possua fallback multi-provedor (Gemini + Groq) e validação em dois níveis, a topologia inicial é linear e qualquer reprovação no nó `quality_reviewer` obriga o `resume_generator` a reescrever o currículo inteiro (~1.500+ tokens de saída). Veja `proposal.md` para a motivação detalhada.

## Goals / Non-Goals

**Goals:**
- Implementar paralelismo Fan-out / Scatter-Gather no LangGraph entre a análise da vaga e a listagem do GitHub.
- Criar o nó cirúrgico `section_patcher` para reescrever exclusivamente blocos rejeitados de forma pontual (*minor*).
- Prover a tool `get_repo_deep_dive` para que o gerador acesse o extrato técnico do README apenas dos repositórios que optar por detalhar.
- Otimizar o arranjo de mensagens para maximizar o reuso de Prompt Caching (prefixos estáticos).
- Integrar `graph.stream(stream_mode="updates")` com a interface Streamlit para visualização em tempo real.

**Non-Goals:**
- Alterar o esquema relacional ou de segurança RLS no Supabase.
- Substituir o framework LangGraph por bibliotecas proprietárias ou loops manuais de thread.
- Modificar o algoritmo determinístico de scoring do ATS (mantido na base 50-98).

## Decisions

### 1. Fan-out Nativo no LangGraph com Nó de Sincronização (`relevance_ranker`)
- **Decisão:** Conectar o ponto de entrada `START` diretamente a dois nós paralelos (`job_analyzer` e `github_fetcher`), convergindo ambos para o nó `relevance_ranker`.
- **Alternativa Considerada:** Disparar threads assíncronas com `asyncio.gather` dentro de uma única função.
- **Razão:** O LangGraph foi projetado para gerenciar concorrência de nós nativamente no grafo, preservando rastreabilidade de estado, telemetria e checkpoints.

### 2. Refinamento Cirúrgico via `section_patcher` e Splice Regex
- **Decisão:** O revisor classifica as rejeições em `minor` (formatação, tabela de habilidades, links de repositório, parágrafo pontual) ou `major` (invenção factual de cargos ou divergência estrutural severa). Para `minor`, o novo nó `section_patcher` recebe apenas o bloco Markdown afetado e a instrução, e uma rotina em Python realiza o *splice* no documento existente.
- **Alternativa Considerada:** Enviar o documento inteiro com prompt de *"corrija apenas o erro"*.
- **Razão:** LLMs tendem a regerar o documento todo de qualquer forma quando recebem o texto completo, gastando os mesmos tokens e correndo risco de regressão em partes que já estavam corretas.

### 3. Tool-Calling Sob Demanda para READMEs de Portfólio
- **Decisão:** Passar no prompt do `resume_generator` apenas os metadados leves (Nome, Descrição, Tags e Score) dos Top 3 repositórios e amarrar a ferramenta `get_repo_deep_dive(repo_name)`.
- **Alternativa Considerada:** Concatenar todos os READMEs pré-baixados no prompt de entrada como texto fixo.
- **Razão:** Se o currículo só citar 1 projeto em destaque ou focar nas experiências profissionais, os tokens de entrada dos outros READMEs são economizados integralmente. Em modelos com suporte a ferramentas, isso segue o padrão moderno de agentes funcionais.

### 4. Ordem Estável de Mensagens para Prompt Caching
- **Decisão:** Padronizar as mensagens em:
  1. `SystemMessage` com regras canônicas de ATS e layouts (fixo, idêntico em todas as execuções).
  2. `HumanMessage` parte 1: Currículo Base do candidato (estático por usuário).
  3. `HumanMessage` parte 2: Vaga e orientações voláteis (sempre no final).
- **Razão:** Os provedores Gemini e Groq preservam cache de contexto nos servidores baseado em prefixo contínuo idêntico de tokens.

### 5. Consumo de Streaming no Streamlit
- **Decisão:** Iterar sobre `graph.stream(initial_state, stream_mode="updates")` dentro de `st.status` no Streamlit, atualizando o checklist visual de etapas conforme cada nó conclui sua execução e renderizando o texto gerado progressivamente via `st.empty()`.
- **Razão:** Elimina o efeito de "tela travada" e diminui drasticamente a sensação de espera do usuário.

## Risks / Trade-offs

- **[Risco: Modelos de contingência que não suportem tool binding]** → *Mitigação:* Se o modelo de fallback ativo não suportar bind de ferramentas, o sistema injeta os extratos de README já limpos como fallback no prompt sem quebrar o fluxo.
- **[Risco: Splice de seção falhar se o modelo alterar o cabeçalho Markdown]** → *Mitigação:* O substituidor busca os limites de seção por regex flexível (`(?im)^##+\s+...`). Se não localizar com segurança, aciona o fallback para substituição conservadora.
- **[Risco: Overhead de latência em conexões lentas do Streamlit Cloud]** → *Mitigação:* As atualizações de streaming no Streamlit são agrupadas por blocos e eventos de nós para não sobrecarregar o tráfego de WebSockets da UI.
