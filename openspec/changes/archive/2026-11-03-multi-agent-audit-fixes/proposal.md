# Proposal: Correções da auditoria do pipeline multi-agente

## Why

A auditoria do pipeline em 03/11/2026 mostrou que a trava factual, a principal promessa do produto, falha em casos comuns. Um currículo com uma tecnologia que o candidato não tem pode ser salvo como aprovado e sem nenhum aviso. Além disso, o matcher dá como comprovadas tecnologias "irmãs" (PostgreSQL por MySQL, Jest por pytest) e o revisor por modelo dá nota ATS sem ver a vaga. Os 140 testes passam porque nenhum cobre esses cenários. Todos os casos foram reproduzidos com o LLM mockado.

## What Changes

**Trava factual e loop de revisão**
- A correção vai para a seção onde a lacuna aparece, não mais sempre para a de habilidades. Lacuna no cabeçalho (título do cargo) leva à regeneração completa no modo rígido.
- Se ainda houver defeito crítico na versão final, o currículo é salvo com `reviewer_approved=False` e um aviso em `errors`, nos dois modos. O modo econômico deixa de "aprovar com avisos" um currículo com violação.
- A validação determinística passa a acusar currículo vazio e saída cortada pelo limite de tokens do modelo.
- A seção indicada pelo revisor por modelo é conferida com os títulos reais do currículo, inclusive quando vem em outro idioma (PT/EN/ES). Se não existir, a falha vira regeneração em vez de um patch que não altera nada.
- O revisor por modelo passa a receber a vaga (resumo e termos ATS) e as listas de tecnologias comprovadas e de lacunas.

**Matcher de competências**
- **BREAKING** (resultado): as equivalências ficam direcionais. Sinônimos valem nos dois sentidos. Em famílias, o item específico prova o genérico (MySQL prova SQL), mas nunca um irmão. PostgreSQL deixa de ser comprovado por MySQL, Jest por pytest, NestJS por Express, RAG por LLM e RabbitMQ por "mensageria". Por isso, novas otimizações podem ter nota ATS menor e mais lacunas.
- Termos curtos e ambíguos (C, R, Go, REST, TS, ML) passam a exigir a grafia técnica e fronteiras próprias. C não casa mais com C# ou C++, R não casa com "R&D" e Go não casa com "go-live".
- Matcher, validador e prompts passam a usar uma única base de evidências: currículo base, mais nome, descrição e linguagem dos repositórios selecionados, mais os extratos dos READMEs.

**Carta de apresentação**
- A carta recebe as tecnologias comprovadas e as lacunas. Uma lacuna só pode aparecer como disposição para aprender, nunca como experiência. Marcadores `<...>` não preenchidos na carta geram aviso.

**Monitor de cota**
- Sai a sincronização com a pasta `history/`, que contava cada otimização duas vezes. Saem também os campos `synced_history_files` e `manual_reset` e a nota "Inclui N currículos" da tela Sistema.
- Tokens e provedor passam a vir das respostas reais de cada chamada, inclusive nas saídas estruturadas e quando o Groq responde no lugar do Gemini.
- A gravação do arquivo de cota passa a ser protegida contra sessões simultâneas no mesmo processo.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `resume-optimization`: revisão que localiza o defeito, não aprova currículo com defeito crítico e detecta saída vazia ou truncada; modo econômico com aviso visível; mapeamento de competências direcional e com base de evidências única; carta de apresentação ciente das lacunas.
- `ats-optimization`: pontuação que não aceita tecnologias irmãs nem termos ambíguos como correspondência, e nota do revisor por modelo calculada com a vaga.
- `interview-prep-and-gap-analysis`: orientações de entrevista do revisor por modelo baseadas na vaga e nas lacunas reais.
- `quota-and-token-monitoring`: cada chamada contada uma única vez, atribuída ao provedor que de fato respondeu, sem perder registros com sessões simultâneas.

## Impact

- **Código:** `src/core/competency_matcher.py`, `src/agents/nodes.py`, `src/agents/graph.py`, `src/agents/state.py`, `src/core/quota_manager.py`, `src/ui/settings_view.py`, `tests/test_competency_matcher.py`, `tests/test_nodes.py`, `tests/test_quota_manager.py` e um novo teste de fluxo do loop de revisão.
- **Dependências:** nenhuma nova; o callback de uso de tokens já faz parte do `langchain-core` instalado.
- **Dados:** os diagnósticos já salvos não são recalculados. Arquivos de cota antigos com `synced_history_files` ou `manual_reset` continuam sendo lidos, e esses campos são ignorados.
- **Ordem com outras changes:** `system-audit-remediation` (38/42 tarefas) também modifica "Revisar currículo gerado" e "Controle modular de etapas e economia de tokens". Os deltas desta change partem do texto daquela, então ela deve ser arquivada antes desta.
- **Fora de escopo:** detectar de forma determinística se a carta reivindica uma lacuna como experiência; corrigir mais de uma seção na mesma rodada; trava entre processos (vários workers) para o arquivo de cota; recalcular candidaturas antigas.
