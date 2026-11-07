# Tasks

## 1. Desacoplamento de Prompts, Contexto, Scoring e Validador em `src/agents/`

- [x] 1.1 Criar `src/agents/shared/deterministic_validator.py` extraindo `_validate_resume_deterministic` e `_critical_patch_section` de `src/agents/nodes/reviewer.py`, mantendo re-exports em `reviewer.py` e validando com `pytest tests/test_nodes.py`
- [x] 1.2 Criar o subpacote `src/agents/prompts/` (`analysis_prompts.py`, `writer_prompts.py`, `reviewer_prompts.py`) e os módulos compartilhados `src/agents/shared/context.py` e `src/agents/shared/github_scoring.py`, eliminando prompts chumbados e importações cruzadas entre `analysis.py`, `github.py`, `writer.py` e `reviewer.py`
- [x] 1.3 Limpar arquivos `.pyc` órfãos de `src/agents/__pycache__/` referentes a módulos antigos (`nodes.cpython-*.pyc`, `analysis.cpython-*.pyc`, `github.cpython-*.pyc`, `reviewer.cpython-*.pyc`, `writer.cpython-*.pyc`) e verificar que `src/agents/__pycache__/` contém apenas artefatos dos módulos vigentes

## 2. Subpacote de Formatação de Currículo (`src/core/formatting/`)

- [x] 2.1 Criar `src/core/formatting/__init__.py`, `src/core/formatting/styles.py`, `src/core/formatting/markdown_parser.py` e `src/core/formatting/html_renderer.py` separando a folha de estilo A4, o parser/serializador Markdown e o renderizador HTML com sanitização XSS
- [x] 2.2 Atualizar `src/core/resume_formatter.py` para atuar como fachada limpa re-exportando `format_resume_to_html`, `parse_resume_markdown`, `serialize_resume_markdown`, `in_experience_or_projects`, `_inline_format` e `_format_contact_item`, verificando com `pytest tests/test_resume_formatter.py`

## 3. Subpacote de Armazenamento Local e Datas (`src/core/storage/`)

- [x] 3.1 Criar `src/core/storage/__init__.py`, `src/core/storage/date_utils.py` e `src/core/storage/local_store.py` extraindo utilitários de conversão/formatação de data e leitura/serialização de arquivos `.md` locais
- [x] 3.2 Refatorar `src/core/history_manager.py` para delegar operações de data e serialização local a `src/core/storage/` preservando todos os pontos de mock e re-exports, verificando com `pytest tests/test_history.py`

## 4. Desacoplamento de Tema e Sub-painéis na Camada `src/ui/`

- [x] 4.1 Criar `src/ui/theme.py` extraindo `THEME_TOKENS`, `_CSS`, `apply_theme` e `render_footer` de `src/ui/components.py`, mantendo re-exports em `src/ui/components.py` e validando com `pytest tests/test_app_views.py`
- [x] 4.2 Criar `src/ui/application_tabs.py` extraindo as abas de visualização/edição (`render_a4_preview_tab`, `render_resume_editor_tab`, `render_cover_letter_tab`) de `src/ui/applications_view.py`, validando com `pytest tests/test_app_views.py`

## 5. Verificação de Integração e Documentação

- [x] 5.1 Executar a suíte completa `pytest` e adicionar testes unitários diretos para os novos submódulos (`src/core/formatting/`, `src/core/storage/`, `src/agents/shared/deterministic_validator.py`, `src/ui/theme.py`), garantindo 100% de aprovação
- [x] 5.2 Atualizar a árvore de diretórios no `README.md` refletindo a nova distribuição de pastas e módulos
