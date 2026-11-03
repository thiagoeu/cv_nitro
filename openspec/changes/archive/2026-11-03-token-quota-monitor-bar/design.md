# Design

## Context

A tela de Sistema (`src/ui/settings_view.py`) atualmente mostra apenas badges booleanos (`Ativo`/`Inativo`) baseados na presença das chaves `GEMINI_API_KEY`, `GROQ_API_KEY` e `GITHUB_TOKEN` no `.env`. Como a API REST do Google Gemini (AI Studio) não fornece um endpoint público de consulta de saldo de tokens remanescentes da conta gratuita, é necessário combinar **telemetria local persistente de consumo diário (tokens e requisições)** sobre os limites conhecidos do Free Tier (ou limites configuráveis no `.env`) com **consulta em tempo real ao endpoint `/rate_limit` do GitHub**. Veja `proposal.md` para a motivação completa.

## Goals / Non-Goals

**Goals:**
- Rastrear com precisão os tokens consumidos (`usage_metadata` do LangChain ou estimativa por caracteres quando o modelo estruturado omitir metadados) e o total de requisições feitas no dia para Gemini e Groq.
- Persistir os contadores diários em `profiles/quota_usage.json` (com reset automático por data `YYYY-MM-DD`) para que o medidor sobreviva a recarregamentos de página (F5) e reinícios do servidor.
- Exibir em `src/ui/settings_view.py` barras visuais (`st.progress`) com a **porcentagem restante** (ex.: `92% restante`), estimativa de quantas otimizações completas ainda podem ser rodadas hoje (~4.500 tokens / ~4 requisições por otimização média) e alertas claros quando restar menos de 15%.
- Consultar sob demanda ou em cache curto o endpoint `https://api.github.com/rate_limit` para mostrar a barra real de requisições restantes da API do GitHub.

**Non-Goals:**
- Consultar APIs de faturamento corporativo do Google Cloud Billing (que exigiriam OAuth/Service Account IAM fora do escopo do AI Studio Free Tier).
- Bloquear a execução do usuário caso o medidor estimado chegue a 0% (o sistema exibirá alerta crítico, mas ainda permitirá tentar ou usar o fallback Groq).

## Decisions

1. **Rastreamento Híbrido (Metadados Reais + Estimativa por Caracteres) em `src/core/quota_manager.py`**
   - *Decisão*: Criar `record_llm_usage(provider: str, tokens: int, requests_count: int = 1)` e um helper `extract_or_estimate_tokens(response, prompt_text: str = "") -> int` que lê `response.usage_metadata.get("total_tokens")` (padrão LangChain para `ChatGoogleGenerativeAI` e `ChatGroq`) e, no caso de chamadas `with_structured_output` que retornam diretamente um objeto Pydantic (`JobAnalysis` ou `ReviewResult`), estima os tokens por `max(1, (len(prompt_text) + len( result.model_dump_json() )) // 4)`.
   - *Racional*: Mantém compatibilidade total com todos os mocks e testes existentes de `with_structured_output` sem alterar o contrato de retorno dos nós em `src/agents/nodes.py`.

2. **Orçamento Diário Configurável com Padrões Realistas de Free Tier**
   - *Decisão*: Definir em `src/core/config.py` limites diários padrão configuráveis via `.env`:
     - `GEMINI_DAILY_TOKEN_LIMIT` (padrão: `250000` tokens/dia de margem segura operacional) e `GEMINI_DAILY_REQUEST_LIMIT` (padrão: `250` req/dia no Free Tier).
     - `GROQ_DAILY_TOKEN_LIMIT` (padrão: `200000` tokens/dia) e `GROQ_DAILY_REQUEST_LIMIT` (padrão: `500` req/dia).
   - *Racional*: A porcentagem restante exibida na barra será o **menor percentual restante** entre cota de tokens e cota de requisições (`min(remaining_tokens_pct, remaining_requests_pct)`), pois no Free Tier do Gemini o limite de requisições diárias (RPD) costuma esgotar antes do limite de tokens (TPD).

3. **Cálculo de "Quantas Otimizações Restam" e Semáforo Visual em `settings_view.py`**
   - *Decisão*: Considerar o custo médio empírico de 1 otimização completa no CV Nitro (~4 chamadas LLM e ~4.500 tokens) para calcular `remaining_runs = min(remaining_requests // 4, remaining_tokens // 4500)`. Exibir barra de progresso com `st.progress(remaining_pct / 100, text=...)` e badge colorido (`:green-badge` para $\ge 50\%$, `:orange-badge` para $15\%–49\%$, `:red-badge` para $< 15\%$).

## Risks / Trade-offs

- **[Risk] Uso da chave de API em outra ferramenta externa fora do CV Nitro** → **Mitigação**: Adicionar na tela de Sistema um botão **"Testar disponibilidade dos modelos (Ping)"** e um botão **"Zerar contadores do dia"**, permitindo validar se a chave responde sem erro `429` em tempo real.

