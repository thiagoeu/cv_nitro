# Proposal

## Why

Atualmente, a seção **PROJETOS EM DESTAQUE** (`KEY PROJECTS` / `PROYECTOS DESTACADOS`) do currículo é povoada automaticamente com os 3 repositórios selecionados pelo `relevance_ranker` durante a geração inicial. Porém, muitas vezes o candidato quer incrementar o currículo adicionando manualmente outros projetos específicos por link do GitHub (um por vez ou vários de uma vez), mantendo exatamente a mesma formatação executiva ATS, idioma da vaga, voz em 1ª pessoa e estrutura de bullets do documento, sem precisar rodar toda a otimização do zero nem escrever o Markdown na mão.

## What Changes

- **Nova seção "Incrementar Projetos por Link (GitHub + IA)" na aba do Currículo (`src/ui/application_tabs.py`)**:
  - Adicionar um painel interativo no editor do currículo onde o usuário pode informar um ou mais links de repositórios do GitHub (ex.: `https://github.com/usuario/repositorio`) e clicar em **"Adicionar projeto(s) ao currículo"**.
  - Permitir uso incremental repetido: a cada novo link enviado, o sistema busca os dados do repositório, gera o bloco do projeto no padrão canônico do documento e **acrescenta (incrementa)** ao final da seção `PROJETOS EM DESTAQUE` existente, preservando os projetos já presentes (ou atualizando caso o mesmo link já exista) e recompilando a folha A4 automaticamente.
  - Incluir trava de execução concorrente (`disabled=True` no botão e alerta contra `F5` enquanto a IA processa o link).
- **Coleta Individual de Repositório e Formatação Canônica via IA (`src/agents/shared/project_injector.py` e `src/agents/prompts/writer_prompts.py`)**:
  - Extrair `owner/repo` da URL do GitHub informada, consultar os metadados e o `README.md` higienizado via API REST do GitHub (`_github_headers()`, `_clean_readme()`).
  - Invocar o modelo via `llm.invoke_tracked` com `PROJECT_INJECTOR_PROMPT` para redigir o bloco do projeto estritamente no padrão do currículo (`### <Nome> — <Proposta de valor>`, `*<Stack>*`, bullets `- **<Pilar técnico>:** <ação em 1ª pessoa>` e `- **Repositório:** <URL>`), no idioma da candidatura (`pt`, `en`, `es`) e alinhado ao contexto da vaga.
  - Inserir o novo projeto de forma incremental na seção de projetos do Markdown e persistir a atualização no histórico/Supabase.

## Capabilities

### New Capabilities

<!-- Nenhuma nova capacidade raiz; estende a capacidade existente resume-optimization. -->

### Modified Capabilities

- `resume-optimization`: Adiciona o requisito de incremento sob demanda de projetos em destaque a partir de links de repositórios do GitHub, mantendo o padrão estrutural e o idioma do currículo.

## Impact

- **Código Afetado**:
  - Novo módulo `src/agents/shared/project_injector.py` (validação de URL do GitHub, coleta de metadados + README, chamada ao LLM e inserção incremental na seção de projetos do currículo).
  - `src/agents/prompts/writer_prompts.py` e `src/agents/prompts/__init__.py` (adição de `PROJECT_INJECTOR_PROMPT`).
  - `src/ui/application_tabs.py` e `src/ui/applications_view.py` (seção visual de adição de projetos por link na aba do currículo, passando idioma e contexto da vaga).
  - `src/ui/navbar.py` (limpeza do estado transitório `proj_inject_is_generating` em `clear_transient_state`).
- **Testes**:
  - Novos testes unitários cobrindo parsing de URL do GitHub, formatação via LLM mockado, inserção incremental sem sobrescrever projetos anteriores e proteção de botão na UI.

