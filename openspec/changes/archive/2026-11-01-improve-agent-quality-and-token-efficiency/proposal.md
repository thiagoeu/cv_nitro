# Proposal: improve-agent-quality-and-token-efficiency

## Why
O pipeline atual de agentes do CV Nitro sofre com seleção fraca de repositórios no GitHub (pega os primeiros sem critério de relevância ou tratamento de forks), truncamento excessivo de evidências técnicas dos READMEs (400 caracteres que impedem extração de realizações reais), revisor baseado puramente em LLM sem validações determinísticas de baixo custo, e pontuação de score ATS arbitrária/alucinada. Esta mudança corrige a seleção de projetos, introduz verificações determinísticas com zero custo de tokens, melhora a fidelidade dos dados do portfólio e ancora o cálculo de ATS em métricas reais de cobertura.

## What Changes
- **Seleção Inteligente no GitHub Researcher**:
  - Filtro para ignorar repositórios marcados como `fork` (foco em autoria do candidato).
  - Ponderação e ranqueamento determinístico considerando correspondência exata de linguagens, tópicos do repositório (`topics`), descrição sem falsos positivos (utilizando regex/word boundaries em vez de substring pura) e atividade/estrelas.
  - Tratamento explícito de falhas da API do GitHub (rate limits 403, timeouts, 404), populando a lista `errors` do estado para comunicação transparente com a interface do usuário.
- **Higienização e Enriquecimento Inteligente de READMEs**:
  - Limpeza prévia de badges, links de licença, imagens e seções de instalação irrelevantes.
  - Aumento da janela útil de evidência técnica para ~1.200 caracteres limpos por repositório para o gerador de currículo e carta de apresentação, preservando a cota de tokens sem perder substância técnica.
- **Validação Determinística Prévia no Quality Reviewer (Zero-Token Guardrails)**:
  - Validação determinística de conformidade estrutural (formato da tabela Markdown de 2 colunas, ausência de placeholders residuais como `<...>`, checagem de seções canônicas).
  - Checagem determinística de integridade de repositórios: garantia de que qualquer link/repositório citado no currículo gerado realmente existe na lista consultada do GitHub.
  - Modo econômico (`strict_review=False`) aprimorado: executa toda a validação determinística e cálculo real sem realizar nenhuma chamada extra ao modelo de linguagem.
  - Em modo rigoroso (`strict_review=True`), falhas estruturais ou de link são rejeitadas precocemente com mensagens estruturadas, evitando invocações desnecessárias da LLM auditora.
- **Score ATS Auditável e Baseado em Métricas Reais**:
  - Substituição de notas heurísticas fixas (80, 85, etc.) por um cálculo ponderado baseado em:
    * Cobertura percentual de tecnologias da vaga presentes no currículo.
    * Cobertura de palavras-chave ATS.
    * Pontuação de conformidade com padrões estruturais de ATS.
- **Alinhamento Contextual da Carta de Apresentação**:
  - Fornecimento de resumos técnicos concisos (1 a 2 linhas) dos projetos selecionados para a Cover Letter, evitando cartas genéricas sem estourar o limite de tokens.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability durável criada; as melhorias se integram às capabilities existentes do ecossistema de otimização de currículo e ATS. -->

### Modified Capabilities
- `resume-optimization`: Refinamento da seleção inteligente de repositórios do GitHub, enriquecimento limpo de READMEs, validação determinística de integridade no revisor e tratamento de erros de API.
- `ats-optimization`: Substituição de score estimado por cálculo determinístico e auditável de compatibilidade ATS baseado em aderência de tecnologias e palavras-chave.

## Impact
- **Arquivos afetados**:
  - `src/agents/nodes.py`: reestruturação de `github_researcher`, `resume_generator`, `quality_reviewer` e `cover_letter_generator`.
  - `src/agents/state.py`: suporte opcional para métricas detalhadas do diagnóstico ATS e estrutura de repositórios ranqueados.
  - `tests/`: inclusão de testes unitários para ranqueamento determinístico, limpeza de READMEs e cálculo de score ATS.
- **Dependências**: Nenhuma biblioteca externa nova necessária (usa `requests`, `re` e funções utilitárias padrão do Python).
