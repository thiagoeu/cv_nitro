# Tasks: Corrigir chamadas LLM, tradução e formatação

## 1. Chamadas LLM e propagação de erros

- [x] 1.1 Criar `_llm()` (modelo, temperatura, timeout, `thinking_level`) e `_text()` (string de `response.text`, sem cercas ```` ``` ````) em `src/agents/nodes.py` e usá-los em todos os nós — verificar: teste com `AIMessage(content=[{"type": "text", ...}])` retorna string
- [x] 1.2 Adicionar `errors: Annotated[List[str], operator.add]` ao `GraphState`; `job_analyzer`/`resume_generator` propagam exceções; revisor/carta registram em `errors` sem carta falsa — verificar: testes de falha em `tests/test_nodes.py`
- [x] 1.3 Remover `@st.cache_resource` do grafo em `app.py` e exibir `st.warning` para cada item de `errors` nos dois fluxos (nova otimização e re-otimização), preservando os avisos através do `st.rerun()` — verificar: `pytest` + `AppTest` do Streamlit sem exceção e com o aviso exibido
- [x] 1.4 Nova otimização: renderizar o resultado fora do `st.status` (antes ficava escondido no status colapsado) reaproveitando a tela do histórico; trocar `st.components.v1.html` (removido) por `st.iframe` — verificar: `AppTest` da tela do histórico

## 2. Tradução e formato dos prompts

- [x] 2.1 Dict `LABELS` (pt/en/es) com seções, cabeçalho da tabela, categorias e rótulo do repositório; regra explícita de tradução integral no prompt do gerador; bullets `- **Tópico:** ação` sem colchetes — verificar: teste captura o prompt em inglês e não contém "HABILIDADES TÉCNICAS"/"Categoria"
- [x] 2.2 Alinhar o revisor: mesmo formato de bullet, tabela de habilidades em qualquer idioma e reprovação de trechos fora do idioma da vaga — verificar: execução real com vaga EN + currículo PT gera currículo todo em inglês

## 3. Formatação da tabela (HTML) e parser DOCX

- [x] 3.1 Formatador: cabeçalho pela linha separadora e barra de contato só antes da primeira seção — verificar: testes em `tests/test_resume_formatter.py` (cabeçalho `Category`, linha com "GitHub Actions" após seção)
- [x] 3.2 Formatador: remover só o marcador de lista dos bullets (o regex antigo comia o `**` e o HTML mostrava `Tópico:** texto`) — verificar: `<strong>Impacto Nacional:</strong>` no teste do formatador
- [x] 3.3 Parser DOCX na ordem do documento com tabelas como linhas Markdown `| a | b |` — verificar: teste em `tests/test_document_parser.py` com tabela entre parágrafos

## 4. Validação integrada

- [x] 4.1 Rodar `pytest` completo e um fluxo real (vaga EN do histórico + currículo base PT) confirmando idioma `en`, tecnologias preenchidas, currículo/carta em inglês e HTML com tabela correta
