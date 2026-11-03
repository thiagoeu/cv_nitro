# Design

## Context

O grafo multi-agente em `src/agents/graph.py` e `src/agents/nodes.py` já opera sobre o estado tipado `GraphState` (`src/agents/state.py`), com *fan-out* inicial (`job_analyzer` + `github_fetcher`), convergência determinística (`relevance_ranker`) e loop condicional de revisão (`quality_reviewer` → `section_patcher` | `resume_generator` | `cover_letter_generator` | `END`). Contudo, o estado atual não preserva o histórico de decisões dos agentes (`agent_trace`), não guarda o snapshot da melhor versão avaliada durante o loop de refinamento e descarta informações ricas já calculadas (como `missing_keywords` e os scores dos repositórios no `relevance_ranker`). Veja `proposal.md` para a motivação completa.

## Goals / Non-Goals

**Goals:**
- Capturar um rastro estruturado e acumulativo (`agent_trace`) no `GraphState` sem quebrar a execução concorrente do *fan-out* inicial.
- Implementar *Snapshot & Rollback* da melhor versão do currículo (`best_resume_md`, `best_ats_score`, `best_diagnostic`) com critério de parada por estagnação (`no_improvement`) no ciclo entre `quality_reviewer`, `section_patcher` e `resume_generator`.
- Expor no dicionário `diagnostic` (já persistido em JSON no Supabase e nos arquivos locais `history/*.md`) as lacunas reais (`missing_keywords`), os repositórios curados (`curated_repos`), as dicas de entrevista (`interview_tips`) e o rastro de agentes (`agent_trace`).
- Paralelizar o download dos Top 3 READMEs em `relevance_ranker` com `concurrent.futures.ThreadPoolExecutor`.

**Non-Goals:**
- Alterar o schema SQL do Supabase (`applications` já possui a coluna `diagnostic JSONB`, que armazena novos campos sem necessidade de migração DDL).
- Introduzir um novo nó de chamada LLM exclusiva para entrevista que aumente o custo de tokens ou a latência da pipeline: as dicas de entrevista serão geradas de forma determinística/híbrida a partir das lacunas reais (`missing_keywords`), dos projetos curados e do parecer estruturado do `ReviewResult`.

## Decisions

1. **Redutor acumulativo para `agent_trace` no `GraphState`**
   - *Decisão*: Declarar `agent_trace: Annotated[List[Dict[str, Any]], operator.add]` em `GraphState` (`src/agents/state.py`), seguindo o mesmo padrão já validado em `errors: Annotated[List[str], operator.add]`.
   - *Racional*: Como `job_analyzer` e `github_fetcher` executam em paralelo a partir de `START`, um campo comum sem reducer causaria conflito de escrita concorrente (`InvalidUpdateError`) no LangGraph. Com `operator.add`, cada nó retorna `"agent_trace": [{"agent": ..., "step": ..., "detail": ..., "status": ...}]` e o LangGraph concatena as entradas de forma determinística.
   - *Alternativa descartada*: Construir o rastro apenas na camada de UI (`wizard_view.py`) via `graph.stream()`. Descartado porque perderia a visibilidade interna das decisões tomadas dentro de `quality_reviewer` (ex.: se houve restauração de snapshot) e dificultaria testes unitários diretos nos nós.

2. **Snapshot da Melhor Versão e Parada por Estagnação no `quality_reviewer`**
   - *Decisão*: Adicionar ao `GraphState` os campos `best_resume_md: Optional[str]`, `best_ats_score: Optional[int]`, `best_diagnostic: Optional[Dict[str, Any]]` e `stop_reason: Optional[str]`.
   - *Racional*: Em cada avaliação no `quality_reviewer`, se o documento não possuir falhas críticas determinísticas (URLs inventadas ou placeholders abertos) e `final_ats_score > best_ats_score`, o snapshot é atualizado. Se `attempts > 0` e a nova nota não superar `best_ats_score` (ou quando `attempts + 1 >= MAX_REVIEW_ATTEMPTS`), o `quality_reviewer` restaura `generated_resume_md = best_resume_md`, define `stop_reason = "no_improvement"` (ou `"max_attempts"`) e sinaliza encerramento do loop em `route_after_review`, registrando no `agent_trace` que a melhor versão foi preservada.
   - *Alternativa descartada*: Controlar o snapshot fora do LangGraph num loop `while` externo (como faz o repositório `meu-emprego-novo` com CrewAI). Manter o snapshot dentro do `GraphState` preserva o grafo autocontido e compatível com `graph.stream()`.

3. **Cálculo de Lacunas (`missing_keywords`) e Guia de Entrevista sem Custo Extra de Chamada LLM**
   - *Decisão*: Calcular `missing_techs` e `missing_kws` diretamente em `_validate_resume_deterministic` (complemento exato de `matched_techs` e `matched_kws`), incluir um campo opcional `interview_tips: List[str]` no schema Pydantic `ReviewResult` (para o modo `strict_review=True`) com fallback determinístico contextualizado (baseado nos `missing_keywords` e nos `github_repos` selecionados) para o modo econômico (`strict_review=False`).
   - *Racional*: Garante zero chamadas adicionais à API de LLM, mantendo o tempo de resposta rápido e funcionando tanto no modo estrito quanto no modo econômico.

4. **Download Concorrente de READMEs com `ThreadPoolExecutor`**
   - *Decisão*: Substituir o loop sequencial de `requests.get` dos Top 3 repositórios em `relevance_ranker` por `ThreadPoolExecutor(max_workers=3)`.
   - *Racional*: Reduz a latência de I/O de rede de $3 \times \text{RTT}$ para $\approx 1 \times \text{RTT}$, mantendo o mesmo tratamento de timeout (`GITHUB_TIMEOUT`) e higienização via `_clean_readme`.

## Risks / Trade-offs

- **[Risk] Candidaturas antigas salvas no histórico não possuem `agent_trace`, `missing_keywords` ou `curated_repos` no JSON de `diagnostic`** → **Mitigação**: Em `render_ats_diagnostic_panel` (`src/ui/diagnostic_view.py`), usar `.get()` com fallbacks graciosos, renderizando as novas seções e expanders apenas quando os dados estiverem presentes ou exibindo mensagens informativas limpas.
- **[Risk] Restauração de snapshot sobrescrever uma versão onde um erro crítico de placeholder foi corrigido** → **Mitigação**: Só salvar um estado como `best_resume_md` quando `is_valid == True` (sem placeholders residuais nem URLs falsas no Tier 1), ou priorizar sempre uma versão `is_valid == True` sobre uma versão inválida mesmo que o score bruto seja próximo.

