# Tasks

## 1. Matcher de competências (D1, D2, D3)

- [x] 1.1 Em `src/core/competency_matcher.py`, substituir `CANONICAL_EQUIVALENCES` por `ALIASES` e `FAMILIES` e reescrever `matches_technology` para aceitar só sinônimos de `req` e, se `req` for chave de família, os membros dela (D1). Verificar com novos casos em `tests/test_competency_matcher.py`: PostgreSQL×MySQL, Jest×pytest, NestJS×Express, GitLab×GitHub, RAG×LLM e RabbitMQ×"mensageria com Kafka" dão `False`, e SQL×MySQL, Git×GitHub, IA Generativa×RAG dão `True`. Os testes atuais desse arquivo continuam passando sem alteração.
- [x] 1.2 Trocar a fronteira direita por `(?![a-zA-Z0-9+#])` e adicionar `AMBIGUOUS_TERMS` com comparação que diferencia maiúsculas e recusa `&`/`-` colados (D2). Verificar com testes: C×"C#", C×"C++", R×"R&D", Go×"go-live", REST×"the rest of" dão `False`; Go×"APIs em Go.", Go×"golang", REST×"APIs REST", C×"firmware em C" dão `True`.
- [x] 1.3 Criar `candidate_evidence(base_resume, repos, readmes)` e o parâmetro `readmes` em `classify_competencies` (D3). Fazer o nó `competency_matcher` passar `state["github_readmes"]` e o `_validate_resume_deterministic` montar `candidate_bg` com a mesma função. Verificar com teste: Redis presente só no README fica em `verified_technologies` e não gera violação de trava factual quando citado em projetos.

## 2. Validação determinística localizada (D4, D6)

- [x] 2.1 Fazer `_validate_resume_deterministic` retornar os defeitos críticos como `(mensagem, trecho)` e reescrever `_critical_patch_section` para devolver a seção que contém o trecho do primeiro defeito, ou `None` no cabeçalho ou sem trecho (D4). Adaptar as asserções de mensagem em `tests/test_agent_quality_improvements.py` e `tests/test_nodes.py` ao novo formato. Verificar com teste novo: lacuna no resumo resulta em `patch_section` igual ao título do resumo; lacuna no título do cargo em modo rígido resulta em `("major", None)`.
- [x] 2.2 Adicionar `generation_truncated` ao `GraphState`, preenchê-lo em `resume_generator` e `section_patcher` a partir do `finish_reason` e incluir no validador os defeitos críticos de texto vazio e de saída truncada (D6). Verificar com testes: resposta mockada com `response_metadata={"finish_reason": "MAX_TOKENS"}` deixa `generation_truncated=True` e torna o currículo inválido; texto vazio torna o currículo inválido.

## 3. Loop de revisão (D5, D7, D8)

- [x] 3.1 Em `build_result_payload`, quando a rodada encerra o loop e a versão mantida é a atual inválida, gravar `reviewer_approved=False`, `stop_reason="critical_issues_remaining"` e um aviso em `errors`. Remover o ramo "Aprovado em modo econômico com avisos". Fazer `route_after_review` encerrar com qualquer `stop_reason` não vazio (D5). Atualizar `test_economic_mode_patches_critical_issue_once`, porque a segunda passada agora não aprova. Verificar com teste: `stop_reason` desconhecido leva a `END` ou à carta.
- [x] 3.2 Criar `_resolve_section` e aplicá-la ao `target_section` do revisor por modelo antes de `build_result_payload`. Seção não resolvida vira severidade `major` (D7). Verificar com testes: currículo EN com alvo "HABILIDADES TÉCNICAS" resulta em `patch_section="TECHNICAL SKILLS"`; alvo inexistente resulta em `review_severity="major"` e rota `resume_generator`.
- [x] 3.3 Incluir no prompt do revisor por modelo os blocos de vaga (`_job_context`), tecnologias comprovadas e pendências técnicas (D8). Verificar com teste que captura o prompt enviado ao LLM mockado e confere que ele contém o resumo da vaga e uma pendência técnica.
- [x] 3.4 Criar um teste de grafo com LLM mockado que reproduz a auditoria: vaga com a lacuna "Kubernetes" e gerador que a coloca no resumo. Verificar que, nos dois modos, o patcher recebe a seção de resumo. Se o patch remove o termo, o currículo final não contém "Kubernetes". Se o patch não remove, o estado final tem `reviewer_approved=False` e `errors` não vazio.
- [x] 3.5 Atualizar o parágrafo do modo econômico no `README.md` (seção do revisor): o modo econômico não aprova currículo com defeito crítico remanescente e mostra um aviso. Verificar relendo o trecho, que não deve mais dizer "antes de aprovar".

## 4. Carta de apresentação (D9)

- [x] 4.1 Incluir no prompt do `cover_letter_generator` as tecnologias comprovadas, as pendências técnicas e a regra de citar lacunas só como disposição para aprender. Após a geração, adicionar aviso em `errors` quando `_unfilled_placeholders` encontrar marcadores na carta. Verificar com testes: o prompt capturado contém as pendências; uma carta mockada com `<Nome da empresa>` gera aviso e continua salva em `generated_cover_letter_md`.

## 5. Monitor de cota (D10, D11, D12)

- [x] 5.1 Remover de `src/core/quota_manager.py` a sincronização com `history/` e tudo o que só ela usava. Simplificar `_load_usage` e `reset_daily_quota` e retirar `synced_history_count` de `get_quota_status` e a nota correspondente em `src/ui/settings_view.py` (D11). Verificar com teste: 4 registros de uso seguidos de um arquivo `history/<hoje>_*.md` mantêm `requests == 4`. A tela Sistema continua abrindo (`tests/test_app_views.py`).
- [x] 5.2 Criar `_invoke_tracked` em `nodes.py` com `get_usage_metadata_callback`, com fallback para a estimativa atual, e usá-lo nas 5 chamadas de modelo no lugar dos blocos `record_llm_usage` (D10). Verificar com teste em que um chat model fake do `langchain_core` com `model_name="openai/gpt-oss-120b"` responde a uma saída estruturada e o consumo é somado ao Groq. `test_nodes_record_quota_automatically` continua passando.
- [x] 5.3 Proteger com um `threading.Lock` de módulo as sequências ler–alterar–gravar do arquivo de cota, com comentário `ponytail:` sobre o limite de um único processo (D12). Verificar com teste: 8 threads × 25 chamadas de `record_llm_usage` em um arquivo temporário resultam em exatamente 200 requisições.

## 6. Integração

- [x] 6.1 Rodar `venv/Scripts/python -m pytest -q` e verificar que a suíte inteira passa.
- [x] 6.2 Com chaves reais, executar uma otimização em modo econômico e outra em modo rígido para uma vaga com uma tecnologia ausente do perfil. Verificar que a tecnologia não aparece como experiência no currículo nem na carta e que, se aparecer, a candidatura abre com o aviso de pendência crítica. Verificar também que a tela Sistema soma só as requisições daquela execução.

## Workflow follow-up

- Arquivar `system-audit-remediation` antes desta change, porque os deltas de `resume-optimization` partem do texto dela.
- Arquivar esta change depois da revisão e conferir as specs principais resultantes com `openspec validate --strict`.
