# Design

## Context

Ver proposal.md (Why). Estado observado:
- `langchain-google-genai` 4.4 + Gemini 3.x retorna `AIMessage.content` como lista de blocos (`[{"type": "text", "text": ..., "extras": {"signature": ...}}]`). O código usa `response.content` direto, então currículo e carta viram `list` e `history_manager.save_resume` quebra em `.strip()`.
- `app.py` guarda o grafo compilado em `@st.cache_resource`; após o commit que trocou `gemini-1.5-pro` por `config.GEMINI_MODEL`, o processo do Streamlit continuou com os nós antigos.
- Todos os nós capturam `Exception`, fazem `print` e devolvem fallback (`job_language="pt"`, currículo base, carta genérica). O usuário nunca vê o erro.
- Cada chamada com o thinking padrão leva 25–80s; o fluxo completo (analisador + 2× gerador + 2× revisor + carta) passa de 4 minutos.

## Goals / Non-Goals

**Goals:** chamadas LLM corretas e mais rápidas; erro visível; currículo 100% no idioma da vaga; tabela e bullets bem formatados no Markdown e no HTML.

**Non-Goals:** trocar de provedor/modelo, novo layout visual, streaming de progresso por nó, tradução da descrição da vaga.

## Decisions

- **Helper `_llm()` + `_text()` em `nodes.py`.** Um único ponto cria o `ChatGoogleGenerativeAI` (modelo, temperatura, `timeout`, `thinking_level`) e um único ponto extrai o texto (`response.text`, sem cercas ```` ``` ````). Alternativa descartada: tratar a lista em cada nó (4 cópias da mesma lógica).
- **`thinking_level="low"` exceto no gerador de currículo.** Analisador/revisor/carta são tarefas curtas; medido ~30s → ~11s no analisador com o mesmo resultado. O gerador mantém o padrão do modelo por ser a etapa de qualidade.
- **Erros: propagar nos nós críticos, acumular nos opcionais.** `job_analyzer` e `resume_generator` deixam a exceção subir — sem idioma ou sem currículo não há resultado útil, e o `try/except` do app já mostra o erro sem salvar. Revisor e carta adicionam a mensagem em `errors` (`Annotated[list[str], operator.add]` no `GraphState`), e o app exibe `st.warning`. Alternativa descartada: canal de erro para todos os nós com lógica de "salvar ou não" no app — mais código para o mesmo comportamento.
- **Rótulos por idioma em um dict `LABELS` (pt/en/es).** Seções, cabeçalho da tabela, exemplos de categorias e o tópico "Repositório GitHub" vêm do dict; o prompt ganha a regra explícita de tradução. Alternativa descartada: só "escreva em inglês" sem rótulos — o template em português no prompt continuava vazando para a saída (observado).
- **Bullet Markdown `- **Tópico:** ação`.** O `●` literal no Markdown virava bullet duplo no `st.markdown` e os `[colchetes]` do template eram copiados literalmente. O HTML continua desenhando `●`, então a renderização A4 não muda.
- **Formatador:** cabeçalho = linhas antes da linha separadora; barra de contatos só enquanto não houver `section-title` (reusa `in_experience_or_projects`).
- **Parser DOCX:** `Document.iter_inner_content()` (python-docx ≥ 1.1, instalado 1.2) para manter a ordem; tabela vira `| c1 | c2 |`.
- **Sem cache do grafo:** `build_graph()` compila em milissegundos; recompilar a cada rerun elimina a classe de bug de código antigo em memória.

## Risks / Trade-offs

- [Gerador/analisador falhando agora interrompe o fluxo em vez de "funcionar" com fallback] → É o comportamento desejado: o fallback salvava resultados errados. A mensagem mostra a causa (chave, cota, modelo).
- [`thinking_level="low"` pode reduzir a precisão do revisor] → O revisor só valida alucinação/layout/idioma; se reprovar demais, subir para `"medium"` em um ponto (`_llm`).
- [Históricos antigos usam `- ● **`] → O formatador continua removendo `●`/`•` do início dos bullets.
