# Proposal

## Why

Candidatos perdem muito tempo adaptando manualmente seus currículos para cada vaga e falham em destacar os projetos práticos que comprovam os requisitos para os sistemas ATS. Esta mudança propõe a criação do **GitMatch**, um Otimizador Inteligente de Currículos com base no portfólio do GitHub usando uma arquitetura multi-agente.

## What Changes

- Criação da interface em Streamlit para entrada da vaga e currículo base.
- Implementação de um fluxo cíclico no LangGraph (Analisador, Buscador GitHub, Gerador, Revisor).
- Integração com a API do GitHub para metadados e leitura de READMEs.
- Integração com o Google Gemini 1.5 Pro como LLM.
- Criação de um Dashboard (aba de histórico) para acompanhamento e visualização de currículos salvos localmente.

## Capabilities

### New Capabilities
- `resume-optimization`: Coleta a vaga e o portfólio do GitHub para gerar e revisar um currículo aderente utilizando um fluxo multi-agente (LangGraph).
- `resume-history`: Gerencia o armazenamento local e exibe o painel para listar, visualizar e copiar currículos otimizados gerados anteriormente.

### Modified Capabilities
- 

## Impact

- **UI:** Nova interface Streamlit no ar.
- **Integrações:** Adição de chamadas para GitHub API e Google GenAI.
- **Armazenamento:** Criação de estrutura de banco SQLite ou arquivos Markdown para o histórico de currículos.
