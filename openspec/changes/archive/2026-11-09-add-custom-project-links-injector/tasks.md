# Tasks

## 1. Motor de Coleta e Formatação Canônica de Projetos (`src/agents/`)

- [x] 1.1 Adicionar `PROJECT_INJECTOR_PROMPT` em `src/agents/prompts/writer_prompts.py` (e exportar em `src/agents/prompts/__init__.py`) para formatar projetos avulsos no padrão estrito do currículo (`### Nome — Proposta`, `*Stack*`, bullets em 1ª pessoa e `- **Repositório:** <URL>`) no idioma da candidatura
- [x] 1.2 Criar `src/agents/shared/project_injector.py` com `parse_github_repo_urls`, `fetch_single_github_repo`, `generate_project_entry_md`, `append_project_to_resume_md` e `inject_projects_from_urls`, garantindo inserção incremental sem sobrescrever projetos anteriores e atualização sem duplicar URLs repetidas
- [x] 1.3 Adicionar testes unitários em `tests/test_nodes.py` validando parsing de URLs do GitHub, geração do bloco Markdown com LLM mockado, incremento de múltiplos projetos consecutivos e não-duplicação de links repetidos

## 2. Seção de Incremento de Projetos por Link na Interface (`src/ui/`)

- [x] 2.1 Atualizar `render_resume_editor_tab` em `src/ui/application_tabs.py` e sua chamada em `src/ui/applications_view.py` para exibir a seção **"Incrementar Projetos em Destaque por Link (GitHub + IA)"**, com campo de link(s), botão de adição com trava `proj_inject_is_generating`, alerta contra `F5` e salvamento automático com recompilação da folha A4
- [x] 2.2 Incluir `"proj_inject_is_generating"` em `clear_transient_state` de `src/ui/navbar.py` e adicionar testes em `tests/test_app_views.py` verificando a adição incremental de projetos na UI e o bloqueio contra submissão concorrente

