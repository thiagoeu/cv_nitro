# Design

## Context

Conforme detalhado em `proposal.md`, o projeto possui uma separação macro em 3 camadas (`src/agents/`, `src/core/`, `src/ui/`), porém o crescimento orgânico gerou arquivos monolíticos dentro dessas pastas:
- `src/core/resume_formatter.py` (717 linhas): concentra um template CSS A4 de mais de 440 linhas, o parser/serializador estruturado de Markdown e o conversor HTML com sanitização XSS.
- `src/ui/components.py` (417 linhas): mistura 300 linhas de CSS global e tokens de paleta (`THEME_TOKENS`, `_CSS`) com widgets interativos do Streamlit.
- `src/core/history_manager.py` (382 linhas): mistura utilitários de data/fuso horário, leitura/escrita de arquivos `.md` locais com cabeçalho JSON e cliente Supabase.
- `src/agents/nodes/reviewer.py` (375 linhas): mistura o validador determinístico Tier 1 (`_validate_resume_deterministic`, `_critical_patch_section`, cálculo de ATS score e dicas de entrevista) com o nó `quality_reviewer` (auditoria LLM Tier 2 e restauração de snapshot).
- `src/ui/applications_view.py` (360 linhas): concentra a listagem de candidaturas, o painel de re-otimização multi-agente e as abas de edição estruturada/Markdown e carta de apresentação.

A suíte de 162 testes (`tests/`) utiliza `unittest.mock.patch` diretamente nos módulos existentes (ex.: `src.core.history_manager.get_supabase_client`, `src.core.history_manager.get_history_dir`, `src.agents.nodes.reviewer._validate_resume_deterministic`).

## Goals / Non-Goals

**Goals:**
- Distribuir responsabilidades em subpacotes e módulos coesos dentro de `src/agents/`, `src/core/` e `src/ui/`.
- Preservar 100% de retrocompatibilidade de importações e alvos de `unittest.mock.patch` por meio do padrão Facade / Re-export nos módulos originais.
- Remover artefatos órfãos (`__pycache__` de arquivos antigos removidos).

**Non-Goals:**
- Não alterar regras de negócio, prompts de LLM, cálculo de ATS score ou contratos de banco de dados.
- Não mover ou renomear os arquivos de entrada consumidos por `app.py` ou pelos testes sem manter a fachada no caminho original.

## Decisions

1. **Extração do Validador Determinístico em `src/agents/shared/deterministic_validator.py`**:
   - **Decisão**: Mover `_validate_resume_deterministic` e `_critical_patch_section` para `src/agents/shared/deterministic_validator.py` e re-exportá-los em `src/agents/nodes/reviewer.py`.
   - **Racional**: `src/agents/shared/` já abriga utilitários compartilhados pelos nós (`llm.py`, `sections.py`). O nó `reviewer.py` passa a focar apenas no fluxo do agente `quality_reviewer` (Tier 2 LLM + snapshot rollback), reduzindo seu tamanho pela metade.

2. **Criação do Subpacote `src/core/formatting/` com Fachada em `src/core/resume_formatter.py`**:
   - **Decisão**: Dividir `src/core/resume_formatter.py` em:
     - `src/core/formatting/styles.py`: template HTML/CSS A4 (`build_a4_html_document`).
     - `src/core/formatting/markdown_parser.py`: `parse_resume_markdown` e `serialize_resume_markdown`.
     - `src/core/formatting/html_renderer.py`: `format_resume_to_html`, `_inline_format`, `_format_contact_item` e `in_experience_or_projects`.
     - `src/core/resume_formatter.py`: re-exporta todas as funções acima.
   - **Alternativa considerada**: Substituir `src/core/resume_formatter.py` por um diretório `src/core/resume_formatter/`. Descartada porque criaria aninhamento redundante (`src/core/resume_formatter/html_renderer.py`) em vez de um domínio claro `src/core/formatting/`.

3. **Criação do Subpacote `src/core/storage/` com Orquestração em `src/core/history_manager.py`**:
   - **Decisão**: Extrair funções puras de data (`_parse_datetime_naive`, `_get_sort_timestamp`, `format_display_date`) para `src/core/storage/date_utils.py` e utilitários de serialização/leitura de arquivo Markdown local (`COVER_LETTER_DELIMITER`, `_empty_application`, `read_local_file`, `serialize_local_file`) para `src/core/storage/local_store.py`. Manter `get_history_dir`, `get_supabase_client` e as operações públicas em `src/core/history_manager.py` delegando para `local_store` e `date_utils`.
   - **Racional**: Os testes fazem monkeypatch de `src.core.history_manager.get_history_dir` e `src.core.history_manager.get_supabase_client`. Mantendo a resolução de `get_history_dir()` e `get_supabase_client()` em `history_manager.py` (e passando o diretório/caminho para `local_store`), todos os mocks de teste continuam interceptando as chamadas sem precisar alterar uma única linha de teste.

4. **Separação de Tema (`src/ui/theme.py`) e Sub-abas de Candidaturas (`src/ui/application_tabs.py`)**:
   - **Decisão**:
     - Extrair `THEME_TOKENS`, `_CSS`, `apply_theme` e `render_footer` de `src/ui/components.py` para `src/ui/theme.py` (re-exportando em `src/ui/components.py`).
     - Extrair o painel de re-otimização (`render_reoptimization_panel`) e as abas de edição do currículo e carta (`render_resume_editor_tab`, `render_cover_letter_tab`, `render_a4_preview_tab`) de `src/ui/applications_view.py` para `src/ui/application_tabs.py`, mantendo as referências patcháveis em `src/ui/applications_view.py`.

## Risks / Trade-offs

- **[Risco] Quebra de `unittest.mock.patch` em testes unitários ao mover funções entre módulos** → **Mitigação**: Nos pontos onde os testes aplicam `patch("src.ui.applications_view.build_initial_state")` ou `patch("src.core.history_manager.get_history_dir")`, os submódulos recebem as dependências ou mantêm o ponto de interceptação no módulo de fachada original. Rodar `pytest` após cada extração para garantir 100% de aprovação.

