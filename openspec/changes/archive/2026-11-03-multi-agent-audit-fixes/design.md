# Design: Correções da auditoria do pipeline multi-agente

## Context

Motivação em `proposal.md`. Estado atual relevante:

- `competency_matcher.CANONICAL_EQUIVALENCES` é um dicionário de grupos simétricos. `matches_technology(req, texto)` aceita qualquer variante do grupo de `req`, por isso PostgreSQL casa com MySQL. A fronteira de palavra `(?<![a-zA-Z0-9])…(?![a-zA-Z0-9])` deixa `c` casar com `C#` e `C++`.
- A base de evidências está espalhada. O matcher usa currículo base + nome, descrição e linguagem dos repositórios. O validador (`nodes._validate_resume_deterministic`) usa currículo base + nome e descrição. O gerador e o revisor por modelo recebem também os READMEs.
- `nodes._critical_patch_section` identifica o tipo de defeito procurando trechos de texto nas mensagens ("repositório citado", "trava factual") e, quando é trava factual, devolve sempre a seção de habilidades.
- No modo econômico, a segunda passada do `quality_reviewer` aprova o currículo mesmo com defeitos ("Aprovado em modo econômico com avisos") e não grava nada em `errors`.
- `route_after_review` encerra o loop quando `stop_reason` está em uma lista fixa de valores.
- `quota_manager._load_usage` sincroniza `history/` a cada leitura, somando de novo as otimizações que `record_llm_usage` já registrou. Nas saídas estruturadas o resultado é um objeto Pydantic, sem metadados, então o provedor fica sempre "gemini" e os tokens são estimados a partir de parte do prompt.
- Os testes rodam sem rede, com LLM mockado (`tests/conftest.py`).

## Goals / Non-Goals

**Goals:**
- O mesmo conjunto de regras de correspondência e a mesma base de evidências em todos os agentes que decidem o que é fato: matcher, validador, gerador e revisor.
- Saber, a partir do estado final do grafo, se o currículo salvo ainda tem defeito crítico, sem depender de texto livre.
- Cada mudança coberta por um teste mockado que falha no código atual.

**Non-Goals:**
- Mudar o formato do diagnóstico salvo ou recalcular candidaturas antigas.
- Aumentar `MAX_REVIEW_ATTEMPTS` ou corrigir mais de uma seção por rodada.
- Detecção semântica de "reivindicação" na carta de apresentação.

## Decisions

### D1. Equivalências separadas em sinônimos e famílias

O dicionário simétrico é substituído por duas tabelas em `competency_matcher.py`:

- `ALIASES`: conjuntos de grafias do mesmo item, que valem nos dois sentidos. Exemplos: `{html, html5}`, `{postgresql, postgres}`, `{sql server, mssql}`, `{node.js, nodejs, node}`, `{go, golang}`, `{apis rest, api rest, rest api, restful, restful api, restful apis, rest}`, `{inteligencia artificial generativa, ia generativa, generative ai, genai}`, `{machine learning, ml, aprendizado de maquina}`.
- `FAMILIES`: genérico → itens específicos que o comprovam. Exemplos: `sql → {postgresql, mysql, sqlite, mariadb, sql server, tsql, plsql}`, `inteligencia artificial generativa → {rag, llm, ollama}`, `git → {github, gitlab, github actions}`, `mensageria → {rabbitmq, kafka, amqp}`, `node.js → {nestjs, express}`, `testes automatizados → {testes unitarios, testes de integracao, pytest, jest}`, `docker → {docker compose}`, `machine learning → {scikit-learn}`.

`matches_technology(req, texto)` monta as formas aceitas: os sinônimos de `req`; se `req` (ou um sinônimo dele) for chave de família, entram também os membros da família e os sinônimos deles. Os irmãos de `req` nunca entram.

Mudanças de dados com efeito visível: "container", "containerização" e "boas práticas" deixam de comprovar Docker e Clean Code. Já "mensageria" deixa de comprovar RabbitMQ e passa a ser comprovada por ele.

- *Alternativa descartada:* manter o dicionário e passar um parâmetro `strict` nas chamadas. A direção é uma propriedade do dado, não de quem chama; com o parâmetro, cada chamada poderia escolher uma regra diferente.

### D2. Fronteiras e termos ambíguos

- Em todos os termos, a fronteira à direita passa a excluir também `+` e `#`: `(?![a-zA-Z0-9+#])`. Assim C não casa com C++ ou C#, e F não casa com F#.
- `AMBIGUOUS_TERMS = {"c": "C", "r": "R", "go": "Go", "rest": "REST", "ts": "TS", "ml": "ML"}`. Essas formas são comparadas com a grafia técnica exigida, diferenciando maiúsculas (sobre o texto sem acentos mas sem converter para minúsculas). Elas também não podem estar coladas a `&` ou `-`. Isso elimina "R&D", "go-live" e "the rest of" sem perder "Go", "REST" e "R".
- Sinônimos compostos que contêm um termo ambíguo, como "api rest" e "golang", continuam sem diferenciar maiúsculas.
- *Alternativa descartada:* ignorar termos curtos na trava factual. Isso deixaria passar uma alucinação real ("Desenvolvedor Go").

### D3. Uma base de evidências única

`competency_matcher.candidate_evidence(base_resume, repos, readmes) -> str` junta o currículo base, nome, descrição e linguagem dos repositórios e os extratos dos READMEs. `classify_competencies` ganha o parâmetro `readmes`. O nó `competency_matcher` passa `state["github_readmes"]`, e o validador usa a mesma função para montar `candidate_bg`.

- *Alternativa descartada:* tirar os READMEs do prompt do gerador. Eles são a evidência mais rica do portfólio, e a mudança anterior (`system-audit-remediation`) os colocou ali de propósito.

### D4. Defeitos críticos estruturados e localizados

`_validate_resume_deterministic` passa a retornar os defeitos críticos como tuplas `(mensagem, seção)`. Ao registrar cada defeito, o validador já localiza a seção: divide o Markdown pelos títulos `## ` e pega a primeira seção que contém o marcador, a URL ou a lacuna (para a lacuna, usando `matches_technology`). A seção é `None` quando o defeito aparece antes do primeiro `## ` (cabeçalho e título do cargo) ou quando não tem trecho (currículo vazio, saída truncada). As mensagens continuam iguais, então o feedback ao modelo não muda.

`_critical_patch_section(defeitos)` devolve a seção do primeiro defeito localizável. Com isso some a busca por texto nas mensagens. Guardar a seção já resolvida, em vez de um "trecho" para buscar depois, evita refazer a busca e deixa a regra de busca em um único lugar.

Com `None`, o modo rígido usa severidade `major` (regeneração completa, como já acontece para marcador no cabeçalho). O modo econômico não faz patch e cai em D5.

### D5. Versão final com defeito crítico não é aprovada

Em `build_result_payload`, quando a rodada encerra o loop, o sistema verifica se a versão mantida tem defeitos críticos. O loop encerra quando há aprovação, quando há `stop_reason` ou, no modo econômico, quando não há patch possível ou já houve um. Como a versão mantida pode ser a atual ou o snapshot, e o snapshot só guarda versões válidas, basta verificar quando a versão mantida é a atual inválida. Nesse caso:

- `reviewer_approved=False`;
- `stop_reason="critical_issues_remaining"`;
- `errors=["Currículo salvo com pendências críticas: …"]`, que já chega à tela pelo `run_warnings` do diagnóstico.

`route_after_review` passa a encerrar com qualquer `stop_reason` não vazio, em vez de comparar com uma lista. Isso evita que um novo motivo de parada cause um loop esquecido.

- *Alternativa descartada:* não salvar o currículo. A spec "Falhas do modelo visíveis ao usuário" já define o padrão de salvar com aviso para falhas não fatais, e o usuário perderia todo o resto (carta, diagnóstico).

### D6. Currículo vazio ou truncado

- Novo campo de estado `generation_truncated: Optional[bool]`. `resume_generator` e `section_patcher` o preenchem com `response_metadata.get("finish_reason") in {"MAX_TOKENS", "length"}` (valores de Gemini e Groq).
- O validador adiciona um defeito crítico sem trecho quando o texto está vazio e outro quando `generation_truncated` é verdadeiro.
- *Alternativa descartada:* exigir os títulos de resumo e habilidades. O modelo varia os títulos ("SUMMARY" em vez de "PROFESSIONAL SUMMARY"), o que criaria defeitos críticos falsos. E o caso real de seções faltando no fim é justamente o truncamento, que o `finish_reason` já detecta.

### D7. Conferir a seção indicada pelo revisor por modelo

`_resolve_section(md, nome, lang)` compara `nome` normalizado com os títulos `## ` reais. Se nada bater, procura em `LABELS` de todos os idiomas a chave cujo rótulo é igual a `nome` e usa o rótulo do idioma da vaga, se ele existir no currículo. Sem resultado, devolve `None` e a severidade vira `major`. A resolução acontece no `quality_reviewer`, antes de `build_result_payload`. Assim `patch_section` sempre contém um título que existe no currículo.

### D8. Revisor por modelo recebe a vaga

O prompt do `quality_reviewer` ganha três blocos: `_job_context(state)` (já usado pelo gerador e pela carta), as tecnologias comprovadas e as pendências técnicas. São cerca de 300 tokens a mais por revisão, e só no modo rígido.

### D9. Carta ciente das lacunas

O prompt do `cover_letter_generator` recebe as comprovadas e as lacunas, com a regra "lacuna só como interesse ou disposição para aprender". Depois da geração, `_unfilled_placeholders(carta)`, que já existe, gera um aviso em `errors` quando encontra marcadores.

### D10. Uso de tokens pelo callback do LangChain

Novo helper `_invoke_tracked(runnable, entrada, prompt_text)` em `nodes.py`. Ele envolve a chamada em `langchain_core.callbacks.get_usage_metadata_callback()`, que captura `usage_metadata` por `model_name` de toda resposta de chat, inclusive dentro de `with_structured_output` e da cadeia de fallbacks. Para cada modelo capturado, registra 1 requisição e o `total_tokens` no provedor deduzido do nome (a mesma regra de `detect_provider_from_response`, agora sobre o nome). Se o callback não capturar nada (mocks dos testes), mantém a estimativa atual. Os 5 blocos `record_llm_usage(...)` dos nós são substituídos pelo helper.

- *Alternativa descartada:* `with_structured_output(..., include_raw=True)`. Com ela o erro de parsing deixa de gerar exceção, e a cadeia de fallbacks deixaria de trocar de modelo quando a saída vier malformada.

### D11. Fim da sincronização com `history/`

Saem `_estimate_history_file_usage`, `_sync_today_history_into_usage`, `HISTORY_DIR`, `LLM_AGENT_STEPS`, `_DEFAULT_QUOTA_FILE` (só eram usados pela sincronização), os campos `synced_history_files` e `manual_reset`, e `synced_history_count` do `get_quota_status`. `reset_daily_quota` volta a gravar o registro padrão. Em `settings_view.py`, a nota "Inclui N currículos…" é removida. Arquivos antigos com esses campos são lidos normalmente; os campos ficam sem uso e são descartados na próxima gravação, porque `_default_usage` não os inclui.

### D12. Trava no arquivo de cota

Um `threading.Lock` de módulo envolve a sequência ler–alterar–gravar em `record_llm_usage`, `reset_daily_quota` e nas gravações do `probe_live_llm_quotas`. As sessões do Streamlit são threads de um mesmo processo, então isso basta. Marcado com `ponytail:`, já que vários workers exigiriam uma trava de arquivo.

### D13. Contador do Groq depois de uma consulta ao vivo (achado na tarefa 6.2)

Na execução real, o `get_quota_status` mostrava o "usado" do Groq a partir do retrato dos cabeçalhos da última consulta ao vivo (`live_remaining_requests`). Esse retrato nunca avançava, e a tela ficava parada em 1 enquanto o contador local subia. Agora `record_llm_usage("groq")` zera `live_remaining_requests`, do mesmo jeito que o registro no Gemini já zerava `live_exhausted`. A partir daí vale o contador local, que a consulta ao vivo já sincroniza com o servidor.

## Risks / Trade-offs

- [Equivalências direcionais reduzem a nota ATS e aumentam as lacunas em vagas novas] → É o comportamento correto. O efeito fica descrito na proposta como **BREAKING** de resultado, e as candidaturas antigas não são recalculadas.
- [Termo ambíguo escrito em minúsculas no currículo ("experiência em go") deixa de ser reconhecido] → Os sinônimos compostos ("golang") continuam valendo. A lista `AMBIGUOUS_TERMS` é pequena e pode ser ajustada só nos dados.
- [Um README pode citar uma tecnologia que o candidato não usou ("integra com o Kafka do cliente")] → É a mesma evidência que o gerador já recebia. Agora pelo menos todos os agentes concordam sobre ela.
- [Mais regenerações completas no modo rígido (defeito no cabeçalho, seção inexistente)] → O loop continua limitado a `MAX_REVIEW_ATTEMPTS=2`, e hoje essas rodadas já são gastas em patches que não mudam nada.
- [O callback depende de `response_metadata["model_name"]`] → Se o nome vier vazio, o consumo cai na estimativa atual e nada deixa de ser registrado.

## Migration Plan

1. Arquivar `system-audit-remediation` antes desta change, porque os deltas de `resume-optimization` partem do texto dela.
2. Implementar e rodar a suíte completa (`venv/Scripts/python -m pytest -q`).
3. Não há migração de dados. Rollback = reverter o commit; os campos de cota removidos não são necessários para a versão anterior funcionar (ela os recria).

## Open Questions

- A lista inicial de `AMBIGUOUS_TERMS` e das famílias pode precisar de novos termos à medida que aparecerem vagas reais. Isso só afeta os dados do matcher, não o desenho.
