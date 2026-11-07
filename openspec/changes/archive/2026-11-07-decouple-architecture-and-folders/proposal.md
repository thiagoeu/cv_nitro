# Proposal

## Why

À medida que o CV Nitro evoluiu com novas capacidades (validação determinística ATS em duas camadas, editor estruturado de currículo, sincronização híbrida local/Supabase e painel de re-otimização), alguns módulos concentraram múltiplas responsabilidades distintas no mesmo arquivo — especialmente `src/core/resume_formatter.py` (717 linhas misturando folha de estilo CSS A4, parser/serializador Markdown e renderizador HTML), `src/ui/components.py` (417 linhas misturando tokens/CSS global com widgets interativos), `src/core/history_manager.py` (382 linhas misturando persistência local em disco com cliente Supabase) e `src/agents/nodes/reviewer.py` (375 linhas misturando validador determinístico Tier 1 com auditor LLM Tier 2). Desacoplar essas responsabilidades em subpacotes e módulos coesos — mantendo fachadas (re-exports) 100% compatíveis — melhora a legibilidade e a manutenção sem alterar nenhuma regra de negócio severa nem quebrar testes.

## What Changes

- **Desacoplamento do Validador Determinístico em `src/agents/`**:
  - Extrair a lógica determinística de validação ATS e cálculo de score (`_validate_resume_deterministic`, `_critical_patch_section` e regras de checagem de seções/links/placeholders) de `src/agents/nodes/reviewer.py` para `src/agents/shared/deterministic_validator.py`, deixando `src/agents/nodes/reviewer.py` focado no nó `quality_reviewer` (auditoria LLM Tier 2 e rollback de snapshots) e re-exportando as funções para manter compatibilidade total.
  - Remover arquivos `.pyc` órfãos em `src/agents/__pycache__/` referentes a módulos antigos já extintos.
- **Organização de Subpacotes em `src/core/`**:
  - Criar o subpacote `src/core/formatting/` dividindo `src/core/resume_formatter.py` em:
    - `src/core/formatting/styles.py`: template HTML e folha de estilo CSS A4 (`@media print` e modo compacto).
    - `src/core/formatting/markdown_parser.py`: parser e serializador estruturado (`parse_resume_markdown`, `serialize_resume_markdown`).
    - `src/core/formatting/html_renderer.py`: sanitização XSS e conversão Markdown → HTML (`format_resume_to_html`, `_inline_format`, `_format_contact_item`, `in_experience_or_projects`).
    - Manter `src/core/resume_formatter.py` como fachada pública re-exportando todas as funções.
  - Criar o subpacote `src/core/storage/` extraindo utilitários de data (`date_utils.py`) e leitura/serialização de arquivos Markdown locais (`local_store.py`) de `src/core/history_manager.py`, mantendo `src/core/history_manager.py` como orquestrador e fachada compatível com todos os mocks existentes.
- **Desacoplamento de Tema, Componentes e Sub-views em `src/ui/`**:
  - Extrair os tokens de paleta (`THEME_TOKENS`), folha de estilo CSS global (`_CSS`), injeção de tema (`apply_theme`) e rodapé institucional (`render_footer`) de `src/ui/components.py` para `src/ui/theme.py`, mantendo re-exports em `src/ui/components.py`.
  - Dividir `src/ui/applications_view.py` extraindo os painéis especializados (painel de re-otimização e abas de edição estruturada/Markdown e carta de apresentação) para `src/ui/application_tabs.py`, mantendo `src/ui/applications_view.py` enxuto como controlador da listagem e visualização detalhada.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capacidade de negócio introduzida; trata-se de organização arquitetural e desacoplamento modular. -->

### Modified Capabilities

- `modular-ui-architecture`: Amplia os requisitos de modularização para cobrir a separação entre folhas de estilo/tema (`src/ui/theme.py`), widgets reutilizáveis (`src/ui/components.py`), sub-painéis de candidaturas (`src/ui/application_tabs.py`) e subpacotes de domínio (`src/core/formatting/`, `src/core/storage/`, `src/agents/shared/deterministic_validator.py`) preservando fachadas retrocompatíveis.

## Impact

- **Código Afetado**:
  - `src/agents/nodes/reviewer.py` e novo `src/agents/shared/deterministic_validator.py`
  - `src/core/resume_formatter.py` e novo subpacote `src/core/formatting/` (`__init__.py`, `styles.py`, `markdown_parser.py`, `html_renderer.py`)
  - `src/core/history_manager.py` e novo subpacote `src/core/storage/` (`__init__.py`, `date_utils.py`, `local_store.py`)
  - `src/ui/components.py` e novo `src/ui/theme.py`
  - `src/ui/applications_view.py` e novo `src/ui/application_tabs.py`
- **Compatibilidade e Testes**:
  - Zero alterações severas de lógica de negócio e zero quebras de contrato: todos os caminhos públicos de importação e alvos de `unittest.mock.patch` permanecem ativos nas fachadas originais.

