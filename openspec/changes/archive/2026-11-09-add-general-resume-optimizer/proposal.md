# Proposal

## Why

Atualmente o CV Nitro exige obrigatoriamente uma vaga específica (título e descrição completa da vaga) para executar o pipeline de otimização de currículo. No entanto, muitos candidatos desejam também gerar um **currículo geral de alto impacto** — bem estruturado no padrão A4 executivo, destacando todas as suas tecnologias relevantes, experiências e principais repositórios do GitHub — para ter em mãos um documento versátil pronto para envio geral, perfil no LinkedIn ou bancos de talentos, sem alterar o fluxo principal voltado a vagas específicas.

## What Changes

- **Novo Endpoint Independente de Otimização Geral de Currículo**:
  - Criação de um fluxo separado e dedicado (`src/agents/general_workflow.py` e `src/agents/prompts/general_prompts.py`), **sem modificar o grafo (`src/agents/graph.py`), os nós ou os prompts do fluxo principal de vagas específicas**.
  - O novo endpoint recebe o currículo base (obrigatório), o usuário do GitHub (opcional), um título/foco profissional opcional (usando `"Currículo Geral Otimizado"` caso não informado) e o idioma desejado (`pt`, `en` ou `es`).
  - Reaproveita de forma somente-leitura os utilitários de coleta do GitHub (`github_fetcher` e download concorrente de READMEs higienizados), selecionando os melhores repositórios públicos do candidato (por estrelas, riqueza técnica do repositório e alinhamento com o currículo base) e redigindo um currículo completo de alta fidelidade citando as tecnologias relevantes comprovadas na tabela de habilidades, experiências em 1ª pessoa e seção de Projetos em Destaque.
  - Produz um diagnóstico de completude e tecnologias destacadas compatível com a visualização em **Candidaturas**, permitindo pré-visualização A4, **botão/aba de edição completa do currículo** e **adição incremental de projetos específicos por link do GitHub** (tanto durante a geração inicial quanto posteriormente na tela do currículo gerado).
- **Novo Botão Dedicado na Tela do Otimizador (`src/ui/wizard_view.py`)**:
  - Adição de um segundo botão de ação independente (**"Gerar currículo geral de alto impacto (sem vaga específica)"**) ao lado/abaixo do botão original na tela do Otimizador, exigindo apenas o **Currículo base** (dispensando descrição e título de vaga obrigatórios), permitindo informar links de projetos específicos opcionais e mantendo o botão e o fluxo originais 100% intactos.

## Capabilities

### New Capabilities

### Modified Capabilities
- `resume-optimization`: Adição do requisito de otimização geral de currículo sem vaga específica através de um endpoint e botão independentes, preservando integralmente o pipeline existente voltado a vagas.

## Impact

- **Novos Arquivos**:
  - `src/agents/prompts/general_prompts.py`: Prompts dedicados à redação executiva e extração de tecnologias relevantes para o currículo geral sem vaga específica.
  - `src/agents/general_workflow.py`: Endpoint e pipeline independente para geração do currículo geral com enriquecimento via GitHub e diagnóstico de completude.
- **Arquivos Modificados**:
  - `src/agents/prompts/__init__.py`: Exportação dos prompts do fluxo geral.
  - `src/ui/wizard_view.py`: Inclusão do novo botão **"Gerar currículo geral de alto impacto (sem vaga específica)"** e seletor opcional de idioma para o modo geral, sem alterar o botão nem a lógica do fluxo principal.
  - `tests/test_nodes.py` e `tests/test_app_views.py`: Novos testes unitários cobrindo o endpoint geral e o novo botão na UI.

