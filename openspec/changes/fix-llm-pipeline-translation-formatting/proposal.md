# Proposal: Corrigir chamadas LLM, tradução do currículo e formatação da tabela

## Why

Execuções reais (ex.: `history/20261020_182910_*`) salvaram o currículo base sem alteração, idioma `pt` para uma vaga em inglês, tecnologias vazias e uma cover letter genérica de fallback: todas as chamadas ao Gemini falharam e os `except` dos nós engoliram o erro, salvando o resultado como se fosse sucesso. Com o modelo atual (`gemini-3.8-flash`) as chamadas funcionam, mas `response.content` chega como lista de blocos (não string), o prompt fixa rótulos em português (tabela, bullets) mesmo para vagas em inglês, e a tabela de habilidades é extraída do DOCX fora de ordem e renderizada como texto solto/barra de contato.

## What Changes

- **Chamadas LLM:** ler o texto da resposta como string (`.text`), remover cercas ```` ```markdown ````, aplicar timeout e `thinking_level="low"` nos nós auxiliares (analisador, revisor, carta) para reduzir a latência (~30s → ~11s por chamada).
- **Falhas visíveis:** analisador e gerador de currículo propagam o erro (o app mostra a mensagem e não salva lixo no histórico); revisor e carta registram o erro no estado e o app exibe um aviso. Remove a cover letter falsa de fallback.
- **Cache do grafo:** remover `@st.cache_resource` do grafo, que mantinha os nós antigos (modelo `gemini-1.5-pro` desativado) em memória após atualizar o código.
- **Tradução:** instrução explícita para traduzir integralmente o currículo base para o idioma da vaga (pt/en/es), incluindo títulos de seção, cabeçalho/categorias da tabela, tópicos dos bullets e idiomas; nomes próprios e tecnologias não são traduzidos. O revisor passa a reprovar trechos fora do idioma da vaga.
- **Formato coerente gerador ↔ revisor:** bullets em `- **Tópico:** ação` (sem `●`/colchetes literais no Markdown; o `●` é desenhado só no HTML), mesma regra no prompt do revisor.
- **Tabela e bullets no HTML:** cabeçalho detectado pela linha separadora (`| --- |`), não pela palavra "Categoria"; barra de contato só antes da primeira seção; bullets preservam o negrito do tópico (antes saíam como `Tópico:** texto`).
- **Resultado visível:** a nova otimização deixa de renderizar o resultado dentro do `st.status` colapsado e abre a tela da candidatura salva; `st.components.v1.html` (removido no Streamlit) vira `st.iframe`.
- **Parser DOCX:** parágrafos e tabelas extraídos na ordem do documento, com linhas de tabela como Markdown (`| a | b |`).

## Capabilities

### New Capabilities

_Nenhuma._

### Modified Capabilities

- `resume-optimization`: currículo e carta gerados no idioma da vaga (com tradução do conteúdo base), falhas do modelo visíveis ao usuário e nunca salvas como sucesso, e preservação da ordem/tabelas do currículo enviado.

## Impact

- **Código:** `src/agents/nodes.py`, `src/agents/state.py`, `src/core/document_parser.py`, `src/core/resume_formatter.py`, `app.py`.
- **Testes:** `tests/test_nodes.py`, `tests/test_resume_formatter.py`, `tests/test_document_parser.py`, `tests/test_end_to_end_flow.py`.
- **Dependências:** nenhuma nova.
