# Design: Hardening, Security & Quality

## Context
Ver `proposal.md` para motivação e `specs/resume-optimization/spec.md` para requisitos normativos.
A auditoria identificou pontos vulneráveis de injeção XSS em `resume_formatter.py`, requisições HTTP sem timeout em `nodes.py`, comportamento de aprovação indevida do revisor em caso de exceção de rede/API, descarte de dados tabulares em `document_parser.py` e testes com acoplamento a serviços externos e ao diretório de produção `history/`.

## Goals / Non-Goals

**Goals:**
- Sanitizar saídas HTML geradas contra Stored XSS e injeção de tags.
- Proteger chamadas à API do GitHub com validação de regex e timeouts de conexão/leitura.
- Evitar aprovação automática de currículos quando a API do `quality_reviewer` falhar.
- Habilitar extração de texto presente em tabelas de arquivos `.docx` e remover extensão inválida `.doc`.
- Configurar `pytest.ini` para descoberta de pacotes e isolar testes de I/O em pastas temporárias (`tmp_path`).
- Mockar chamadas externas de rede nos testes unitários para garantir execução rápida e determinística.

**Non-Goals:**
- Migração completa para banco de dados relacional (ex: PostgreSQL/SQLite) nesta etapa; a persistência em `.md` será mantida, mas isolada nos testes.
- Alteração no modelo do LangGraph ou criação de novas etapas de nós.

## Decisions

### Decisão 1: Sanitização com `html.escape` antes de formatação inline
- **Decisão:** Aplicar `html.escape()` nos blocos de texto antes de aplicar transformações de markdown (como `**negrito**`, `*itálico*` e links `[texto](url)`).
- **Alternativa rejeitada:** Usar bibliotecas pesadas de terceiros (ex: Bleach / BeautifulSoup) que aumentariam as dependências do projeto desnecessariamente.

### Decisão 2: Validação de usuário GitHub e Timeout explícito
- **Decisão:**
  - Validar nomes de usuário com regex: `re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username)`.
  - Configurar timeout duplo `timeout=(5.0, 10.0)` em todas as chamadas de rede do módulo `nodes.py`.
- **Alternativa rejeitada:** Deixar requisições sem timeout (causa bloqueio permanente de threads no Streamlit).

### Decisão 3: Tratamento de Falha no Quality Reviewer
- **Decisão:** Quando a chamada à LLM do `quality_reviewer` falhar por erro de rede/cota, retornar `reviewer_approved: False` com `reviewer_feedback: "Erro na API de auditoria..."` e não considerar o documento automaticamente aprovado.
- **Alternativa rejeitada:** Manter o fallback atual que aprovava com `reviewer_approved: True`.

### Decisão 4: Extração de Tabelas em DOCX
- **Decisão:** No `extract_text_from_file`, após coletar parágrafos de `doc.paragraphs`, iterar por `doc.tables` e extrair linhas e células não vazias. Remover `.doc` das extensões aceitas.
- **Alternativa rejeitada:** Manter apenas parágrafos (perde habilidades e cargos em currículos estruturados em colunas/tabelas).

### Decisão 5: Higiene de Testes & Fixture Temporária
- **Decisão:** Adicionar `pytest.ini` com `pythonpath = .` e criar em `tests/conftest.py` uma fixture que redireciona `HISTORY_DIR` para `tmp_path`, garantindo que os testes não poluam a pasta `history/` real.

## Risks / Trade-offs

- **[Risco] Falha no revisor pode interromper geração** → *Mitigação:* Como o limite de tentativas (`review_attempts >= 2`) continua existindo, o fluxo é interrompido ou chega a um estado com erro visível em vez de retornar um currículo aprovado às cegas.
- **[Risco] DOCX com tabelas pode duplicar parágrafos se aninhados** → *Mitigação:* Usar conjunto para deduplicação ou formatação limpa de células por linha.
