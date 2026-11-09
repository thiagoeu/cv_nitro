# Tasks

## 1. Prompts e Endpoint Independente de Otimização Geral (`src/agents/`)

- [x] 1.1 Criar `src/agents/prompts/general_prompts.py` (e exportar em `src/agents/prompts/__init__.py`) com `build_general_resume_system_prompt` e `build_general_resume_user_messages` focados em estruturar um currículo executivo A4 de alto impacto destacando todas as tecnologias relevantes comprovadas no currículo base e GitHub, sem exigir vaga específica
- [x] 1.2 Criar `src/agents/general_workflow.py` com `select_top_general_repos`, `extract_highlighted_technologies`, `generate_general_resume` e o endpoint `run_general_optimization`, reutilizando `github_fetcher` e `run_deterministic_checks` de forma somente-leitura sem modificar `src/agents/graph.py` nem os nós existentes
- [x] 1.3 Adicionar testes unitários em `tests/test_nodes.py` validando `run_general_optimization` (com e sem GitHub, extração de tecnologias relevantes e diagnóstico de completude) e verificar com `pytest tests/test_nodes.py`

## 2. Novo Botão de Otimização Geral, Edição e Adição de Projetos na Interface (`src/ui/`)

- [x] 2.1 Atualizar `src/ui/wizard_view.py` adicionando a função auxiliar `run_general_with_status` e a seção de **Currículo Geral (Sem Vaga Específica)** com seletor de idioma, campo opcional para links de projetos desejados do GitHub e o novo botão **"Gerar currículo geral de alto impacto (sem vaga específica)"** (`key="wizard_general_submit_btn"`), preservando intacto o botão e o fluxo originais
- [x] 2.2 Garantir que o currículo geral salvo abra em `src/ui/applications_view.py` com suporte integral ao editor e à seção **"Incrementar Projetos em Destaque por Link (GitHub + IA)"** (incluindo atalho visível para adicionar/editar projetos mesmo sem vaga associada) e adicionar testes unitários em `tests/test_app_views.py` verificando o fluxo completo

