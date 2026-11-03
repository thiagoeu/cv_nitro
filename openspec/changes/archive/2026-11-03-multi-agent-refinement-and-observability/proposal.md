# Proposal

## Why

Embora o pipeline multi-agente atual do CV Nitro conte com execução paralela (*Scatter-Gather*), roteamento cíclico granular (`section_patcher` vs `resume_generator`) e auditoria neuro-simbólica em duas camadas, grande parte dessa inteligência coletiva permanece invisível para o usuário final após a execução. Além disso, insistir em novas rodadas de revisão quando o score ATS não melhora (por conta de uma lacuna real de experiência do candidato) pode pressionar o modelo gerador a alucinar, e o candidato não recebe visibilidade sobre quais requisitos da vaga ficaram de fora nem como se preparar para defendê-los na entrevista.

## What Changes

- **Rastro de Deliberação e Telemetria dos Agentes (`agent_trace`)**: Registro estruturado e acumulativo no `GraphState` de cada passo executado pelos agentes (decisões tomadas, rota escolhida no ciclo de revisão, seção corrigida cirurgicamente, score antes/depois e duração), persistido junto ao diagnóstico e exibido na interface.
- **Snapshot da Melhor Versão e Parada por Estagnação no Ciclo de Revisão**: O `quality_reviewer` passa a manter o snapshot da versão de maior pontuação (`best_resume_md`, `best_ats_score`, `best_diagnostic`). Caso uma revisão subsequente não melhore o score (indicando lacuna real da carreira em vez de falha de redação) ou atinja o limite de tentativas, o fluxo interrompe novas regenerações e restaura automaticamente a melhor versão avaliada.
- **Mapeamento de Lacunas Reais (*Gap Analysis*), Curadoria Visível do GitHub e Guia de Entrevista**: O diagnóstico passa a expor explicitamente as tecnologias e palavras-chave exigidas pela vaga que não constam na base do candidato (`missing_keywords`), os repositórios selecionados pelo `relevance_ranker` com suas respectivas notas de aderência, e um resumo estratégico de preparação para entrevista (pontos fortes a destacar e como responder sobre as lacunas abertas).
- **Download Concorrente de READMEs no `relevance_ranker`**: Paralelização das chamadas HTTP para obtenção dos Top 3 READMEs do GitHub usando `ThreadPoolExecutor`, reduzindo a latência de rede da etapa de curadoria.

## Capabilities

### New Capabilities
- `agent-execution-observability`: Rastreamento estruturado da deliberação entre agentes (`agent_trace`) no estado do grafo e visualização interativa da linha do tempo de decisões, iterações e rotas no painel de diagnóstico.
- `interview-prep-and-gap-analysis`: Identificação explícita de lacunas técnicas e conceituais (`missing_keywords`), exposição do ranking de repositórios do GitHub selecionados e geração de orientações estratégicas de preparação para entrevista baseadas nos gaps reais.

### Modified Capabilities
- `resume-optimization`: Adição de mecanismo de *Snapshot & Rollback* da melhor versão com parada por estagnação de nota no ciclo de revisão (`quality_reviewer` / `route_after_review`) e busca concorrente de READMEs no `relevance_ranker`.
- `ats-optimization`: Expansão do relatório e painel visual de diagnóstico ATS (`render_ats_diagnostic_panel`) para apresentar lacunas técnicas (*gaps*), repositórios curados com score de relevância, guia de entrevista e linha do tempo de execução dos agentes.

## Impact

- **Estado e Grafo de Agentes**: `src/agents/state.py` (`GraphState`), `src/agents/nodes.py` (`job_analyzer`, `github_fetcher`, `relevance_ranker`, `resume_generator`, `section_patcher`, `quality_reviewer`, `cover_letter_generator`) e `src/agents/graph.py` (`route_after_review`).
- **Interface e Persistência de Diagnóstico**: `src/ui/diagnostic_view.py` e `src/ui/wizard_view.py` (persistência transparente dentro do dicionário JSON `diagnostic` já suportado pelo Supabase e pelo armazenamento local em `history/`).
- **Testes Automatizados**: `tests/test_agents.py`, `tests/test_nodes.py` e `tests/test_ui.py`.

