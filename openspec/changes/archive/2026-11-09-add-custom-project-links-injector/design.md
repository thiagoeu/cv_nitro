# Design

## Context

Conforme descrito em `proposal.md`, o currículo gerado possui uma seção canônica de projetos (`## PROJETOS EM DESTAQUE` em PT, `## KEY PROJECTS` em EN, `## PROYECTOS DESTACADOS` em ES), onde cada projeto segue rigorosamente a estrutura:
```markdown
### <Nome do projeto> — <Proposta de valor>
*<Stack separada por vírgulas>*
- **<Pilar técnico>:** <explicação técnica da implementação em 1ª pessoa ('Desenvolvi...', 'Implementei...', 'Estruturei...')>
- **Repositório:** <URL do repositório no GitHub>
```
O usuário deseja uma seção dedicada dentro da aba de edição do currículo (`src/ui/application_tabs.py`) para informar links de projetos do GitHub (um ou mais, e quantas vezes quiser posteriormente) para que a IA leia o repositório e incremente mais projetos nessa seção mantendo o padrão exato do documento.

## Goals / Non-Goals

**Goals:**
- Permitir adicionar projetos por URL do GitHub (`https://github.com/<owner>/<repo>`) diretamente na visualização/edição da candidatura.
- Coletar metadados (`name`, `description`, `language`, `topics`, `html_url`) e o `README.md` higienizado via `_clean_readme` da API do GitHub.
- Gerar o bloco Markdown do projeto via LLM (`llm.invoke_tracked`) seguindo o idioma (`LABELS[lang]`), a voz em 1ª pessoa e o padrão tipográfico do documento.
- Inserir incrementalmente ao final da seção `PROJETOS EM DESTAQUE` sem apagar os projetos anteriores (e sem duplicar se a mesma URL for enviada novamente).
- Proteger o botão de adição contra cliques duplicados e alertar contra `F5` durante o processamento.

**Non-Goals:**
- Não reexecutar o grafo completo de 8 nós apenas para adicionar um projeto.
- Não alterar outras seções do currículo (Resumo, Habilidades, Experiência, Formação).

## Decisions

1. **Módulo Dedicado `src/agents/shared/project_injector.py`**:
   - **Decisão**: Criar funções modulares e testáveis:
     - `parse_github_repo_urls(raw_text: str) -> list[tuple[str, str, str]]`: extrai `(owner, repo, canonical_url)` de uma ou mais URLs do GitHub (aceitando links separados por linha, vírgula ou espaço, limpando sufixos `.git`, `/tree/...` ou `/` final).
     - `fetch_single_github_repo(owner: str, repo: str) -> dict`: consulta `https://api.github.com/repos/{owner}/{repo}` e `/readme` usando `_github_headers()`, `GITHUB_TIMEOUT` e `_clean_readme()`.
     - `generate_project_entry_md(repo_data: dict, language: str, job_description: str = "") -> str`: utiliza `PROJECT_INJECTOR_PROMPT` (definido em `src/agents/prompts/writer_prompts.py`) + `llm.chat_model(temperature=0.2, thinking_level="low")` para gerar exclusivamente o bloco `### Nome — Proposta...` do projeto em 1ª pessoa.
     - `append_project_to_resume_md(resume_md: str, new_project_entry_md: str, repo_url: str, language: str = "pt") -> str`: localiza a seção de projetos do currículo via `resolve_section(resume_md, L["projects"], L)` (ou cria a seção `## {L["projects"]}` caso não exista). Se o `repo_url` já constar em um sub-bloco `### ` da seção, substitui apenas aquele sub-bloco; caso contrário, concatena o novo bloco ao final da seção usando `splice_markdown_section`.
   - **Racional**: Reaproveita toda a infraestrutura já existente (`_clean_readme`, `_github_headers`, `LABELS`, `resolve_section`, `splice_markdown_section`, `llm.invoke_tracked`) com custo mínimo de tokens (~300 tokens por projeto adicionado).

2. **Interface na Aba de Edição do Currículo (`src/ui/application_tabs.py`)**:
   - **Decisão**: Na aba `:material/edit_note: Editar Markdown` (`render_resume_editor_tab`), adicionar no topo um container destacado (`st.container(border=True)`) intitulado **`:material/add_link: Incrementar Projetos em Destaque por Link (GitHub + IA)`**, contendo:
     - Um campo `st.text_input` (ou `st.text_area` compacto) para colar 1 ou mais links de repositórios do GitHub (`https://github.com/usuario/projeto`).
     - Um botão primário **"Adicionar projeto ao currículo"** (desabilitado enquanto `st.session_state.get("proj_inject_is_generating", False)` for `True`, com aviso de retenção contra `F5`).
     - Ao concluir, chama `save_edit_fn(updated_resume_md, cover_letter_md, ...)` que salva no Supabase/local e recompila a folha A4 instantaneamente.

## Risks / Trade-offs

- **[Risco] Usuário colar link que não é do GitHub ou repositório privado/inexistente (HTTP 404)** → **Mitigação**: Validar o formato da URL com regex antes da chamada e tratar HTTP 404/403 exibindo `st.error` claro sem tocar no currículo salvo.
- **[Risco] Duplicação caso o usuário envie o mesmo link duas vezes** → **Mitigação**: `append_project_to_resume_md` divide a seção de projetos nos blocos `### ` e verifica se a URL canônica (`github.com/owner/repo`) já está presente; se estiver, atualiza o bloco existente em vez de duplicar.

