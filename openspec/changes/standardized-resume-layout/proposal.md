# Proposal: Padronização Estrutural e Visual do Currículo de Alta Fidelidade

## Why

Atualmente, o currículo gerado pela aplicação não segue um padrão visual e estrutural consistente com as melhores práticas de mercado para profissionais de tecnologia e sistemas ATS. Com base no modelo real de referência fornecido pelo usuário, é necessário estabelecer um template estrito de alta fidelidade que apresente cabeçalho limpo, resumo denso, tabela de habilidades técnicas categorizada por áreas e itens de experiência profissional orientados a impacto no padrão `● **Tópico:** Ação + Contexto + Resultado`.

## What Changes

- **Template Estrutural Estrito**:
  - **Cabeçalho Centralizado**: Nome Completo em destaque, Cargo/Área em subtítulo e linha única de contatos (`Localidade | Email | LinkedIn | GitHub`).
  - **Resumo Profissional**: Parágrafo único e denso com senioridade, tecnologias centrais, projetos de grande impacto e vivência técnica.
  - **Habilidades Técnicas em Tabela/Blocos**: Categorização clara em áreas técnicas (Back-end & Arquitetura, Front-end & Mobile, IA & Agentes, Mensageria & Filas, Banco de Dados, DevOps, etc.).
  - **Experiência Profissional Padronizada**: `Empresa — Projeto`, subtítulo com `Cargo | Período | Localidade (Modalidade)` e bullets com a fórmula `● **Tópico de Impacto:** Descrição técnica com métricas e verbos de ação`.
  - **Projetos em Destaque**: `Nome — Subtítulo`, tecnologias em itálico, bullets com detalhes arquiteturais e link do repositório GitHub.
  - **Formação Acadêmica, Certificações e Idiomas**: Seções padronizadas com formatação enxuta e elegante.
- **Atualização dos Prompts dos Agentes**:
  - O `resume_generator` passa a incorporar esse template como contrato rígido de saída em Markdown.
  - O `quality_reviewer` passa a validar se o currículo gerado respeita a estrutura padrão e o formato dos bullets.
- **Visualizador Estilizado e Exportação no Streamlit**:
  - O Streamlit passa a contar com um preview estilizado em folha de currículo (tipografia refinada, linhas divisórias sutis e tabela de habilidades limpa).
  - Adição de opção para exportação em HTML estilizado pronto para impressão ou salvamento em PDF direto pelo navegador.

## Capabilities

### New Capabilities
- `resume-preview-export`: Renderização de alta fidelidade visual em folha de estilo profissional no Streamlit e exportação em HTML/PDF para impressão direta.

### Modified Capabilities
- `ats-optimization`: Atualização das regras de padronização estrutural do currículo para exigir cabeçalho unificado, tabela categorizada de competências e bullets com tópicos de impacto destacados.

## Impact

- **Código Afetado**:
  - `src/agents/nodes.py`: reestruturação do prompt do `resume_generator` com o novo template e ajuste no `quality_reviewer`.
  - `src/core/resume_formatter.py` (novo): utilitário para conversão do Markdown padronizado em HTML estilizado com layout para impressão.
  - `app.py`: inclusão do visualizador de folha estilizada e botão de download/impressão em HTML/PDF além do Markdown puro.
- **Dependências**: Nenhuma nova dependência pesada obrigatória; utiliza HTML/CSS puro com tipografia padrão e compatível com navegadores.
