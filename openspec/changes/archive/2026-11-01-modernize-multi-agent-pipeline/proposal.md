# Proposal

## Why

Atualmente, o pipeline multi-agente do CV Nitro opera de forma estritamente sequencial, bloqueante e com regeneração completa de texto a cada ciclo de revisão. Isso gera latência desnecessária no início do fluxo, consome milhares de tokens redundantes de saída em correções pontuais e bloqueia a percepção de progresso do usuário no Streamlit até a conclusão total do grafo.

A modernização da arquitetura com padrões contemporâneos de Sistemas Multi-Agentes (paralelismo Fan-out/Scatter-Gather, refinamento cirúrgico de seções, tool-calling sob demanda, prompt caching e streaming de execução) torna o sistema significativamente mais rápido, econômico em cotas de API e interativo.

## What Changes

- **Paralelismo Fan-out / Scatter-Gather:** Execução concorrente do `job_analyzer` e do `github_fetcher` no ponto de entrada do grafo LangGraph, sincronizados pelo nó determinístico `relevance_ranker`.
- **Tool-Calling sob Demanda para Repositórios:** O `resume_generator` recebe apenas resumos leves dos repositórios e consome detalhes profundos de README via tool invocada sob demanda (`get_repo_deep_dive`), poupando tokens de entrada.
- **Refinamento Cirúrgico por Seção (*Delta Section Patching*):** Introdução do nó `section_patcher` no grafo. Quando o `quality_reviewer` detecta falhas leves ou de formatação pontual (*minor*), apenas o bloco de texto afetado é reescrito e mesclado ao documento, evitando a reescrita de 600 linhas.
- **Prompt Caching & Otimização de Prefixos:** Reestruturação de prompts para manter prefixos estáticos (regras executivas e formato canônico) e semi-estáticos (currículo base) no início da mensagem, maximizando o reuso de cache em GPU no Gemini e Groq.
- **Streaming de Execução no Streamlit:** Substituição da invocação síncrona `graph.invoke` por `graph.stream(stream_mode="updates")`, exibindo o checklist de progresso dos agentes e o texto gerado em tempo real na interface.

## Capabilities

### New Capabilities
- `pipeline-streaming`: Emissão contínua de eventos de progresso dos nós e geração progressiva de texto do currículo para a interface do usuário.

### Modified Capabilities
- `resume-optimization`: Evolução do fluxo do grafo para suportar execução paralela inicial, consumo de evidências via tools e refinamento cirúrgico em revisões leves.

## Impact

- **Código Afetado:**
  - `src/agents/state.py`: Novos campos no `GraphState` para controle de patch de seção (`patch_section`, `patch_instructions`, severidade da revisão).
  - `src/agents/nodes.py`: Nó `github_fetcher` desacoplado, nó `relevance_ranker`, nó `section_patcher`, suporte a tools no gerador e prefixos de prompt caching.
  - `src/agents/graph.py`: Nova topologia do grafo com bifurcação inicial e branch de patch cirúrgico.
  - `src/ui/wizard_view.py` e `app.py`: Consumo de streaming via `graph.stream()` para exibição progressiva.
- **Dependências & APIs:** Utilização de primitivas existentes de `langgraph`, `langchain_core` e `requests` sem adição de pacotes externos pesados.
- **Compatibilidade:** Mantém retrocompatibilidade total com a persistência no Supabase e histórico local.
