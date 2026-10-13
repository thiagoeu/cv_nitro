# Design

## Context

O projeto GitMatch precisa processar texto livre e conectá-mo a perfis do GitHub usando agentes de inteligência artificial. A solução precisa ser interativa (Streamlit) e apresentar um grafo de fluxo cíclico com passos de revisão (LangGraph).

## Goals / Non-Goals

**Goals:**
- Construir a arquitetura da Prova de Conceito (PoC) rodando localmente de forma rápida e fluida.
- Conectar perfeitamente os 4 agentes no LangGraph: Job Analyzer, GitHub Researcher, Resume Generator, Quality Reviewer.
- Persistir os resultados do LLM de forma persistente e simples na máquina local.

**Non-Goals:**
- Deploy em nuvem ou suporte a multi-tenant (vários usuários logados). A PoC focará em uso single-user rodando localmente.
- Scraper avançado para portais de emprego. A entrada de vagas será feita colando o texto.

## Decisions

- **LangChain / LangGraph:** Selecionado no lugar de CrewAI ou AutoGen pela maior capacidade de controlar as transições de estado e criar loops de validação (revisor mandando o currículo de volta para o gerador).
- **Gemini 1.5 Pro:** Escolhido como modelo fundamental em vez do GPT-4o por causa de sua vasta janela de contexto, permitindo injetar múltiplos arquivos `README.md` completos na mesma requisição.
- **Armazenamento de Histórico (Markdown/Arquivos):** Em vez de usar um banco de dados relacional como SQLite ou PostgreSQL, o histórico de currículos será salvo como arquivos `.md` na pasta local `history/` (com metadados JSON ou YAML Frontmatter), pois facilita muito a visualização em Streamlit e a edição manual se necessário.
- **Interface Streamlit:** Framework escolhido por permitir subir o dashboard em minutos usando código Python nativo.

## Risks / Trade-offs

- **Risco:** O limite de rate-limit da API pública do GitHub pode estourar caso o candidato tenha muitos repositórios.
  - **Mitigação:** Faremos uma requisição primária aos repositórios e usaremos filtragem pelo nome e linguagem. Só baixaremos o README completo dos mais relevantes.
- **Risco:** O revisor entrar em loop infinito se o gerador não conseguir consertar a alucinação.
  - **Mitigação:** Implementaremos um limite rígido de tentativas (ex: max_retries = 2) no estado do LangGraph.
