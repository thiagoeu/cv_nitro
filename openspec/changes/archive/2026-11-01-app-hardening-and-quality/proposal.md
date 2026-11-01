# Proposal: App Hardening, Security & Quality Improvements

## Why

Uma auditoria sênior de código identificou vulnerabilidades de segurança (Stored XSS na exportação HTML, injeções de parâmetros e requisições HTTP sem timeout), falhas arquiteturais no fluxo de agentes (falhas silenciosas em que erros de LLM aprovam currículos sem revisão), perda de dados na extração de tabelas em arquivos DOCX, falso suporte a arquivos `.doc`, e falta de higiene na suíte de testes (testes com falsos-positivos e dependência de rede externa).
Esta mudança implementa o endurecimento (*hardening*) de segurança, confiabilidade no fluxo de agentes, parser robusto de documentos e higiene completa nos testes automatizados.

## What Changes

- **Segurança (XSS & Escaping):** Sanitização estrita com `html.escape` em todos os campos inseridos no HTML gerado em `src/core/resume_formatter.py`.
- **Segurança & Resiliência de Rede:** Adição de timeouts de 10s e validação de nome de usuário GitHub via regex em `src/agents/nodes.py`.
- **Propagação de Erros nos Agentes:** Eliminação do padrão de aprovação silenciosa em falhas de API; o `quality_reviewer` e o grafo registram o status real de erro no estado e alertam o usuário.
- **Extração de Documentos:** Suporte à extração de tabelas (`doc.tables`) em arquivos DOCX no `src/core/document_parser.py` e remoção da extensão legada `.doc` para evitar exceções em runtime.
- **Higiene de Testes & Configuração:** Criação de `pytest.ini` para resolução automática de `pythonpath`, isolamento de testes de histórico com diretório temporário para evitar poluição do repositório, e mocks em testes unitários.

## Capabilities

### Modified Capabilities
- `resume-optimization`: Reforça a resiliência na busca do GitHub (timeouts e validação), a revisão de qualidade (não aprovar currículos em falhas silenciosas de API) e a segurança de renderização.

## Impact

- **Código modificado:**
  - `src/core/resume_formatter.py`
  - `src/core/document_parser.py`
  - `src/agents/nodes.py`
  - `app.py`
  - `tests/*`
- **Novos arquivos:**
  - `pytest.ini`
- **Dependências:** Nenhuma dependência externa necessária; utiliza módulos nativos de Python (`html`, `re`, `unittest.mock`).
