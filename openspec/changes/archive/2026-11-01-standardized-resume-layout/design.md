# Design: Padronização Estrutural e Visual do Currículo de Alta Fidelidade

## Context

O currículo de referência fornecido pelo usuário demonstra um alto padrão de apresentação para a área de tecnologia: cabeçalho minimalista com contatos em linha única, resumo focado em impacto, tabela de habilidades técnicas estruturada em duas colunas/categorias e experiências profissionais com bullet points iniciados por tópicos de impacto destacados (`● **Impacto:** ...`). Para que o gerador de currículos alcance essa qualidade, o prompt do `resume_generator` precisa conter o template canônico e as regras exatas de diagramação, acompanhado de um módulo visual no Streamlit para renderização em folha e exportação limpa.

## Goals / Non-Goals

**Goals:**
- Definir o contrato textual e a gramática do currículo gerado no `resume_generator`, espelhando a estrutura do PDF de referência.
- Padronizar os bullet points de experiência e projetos no formato `● **Tópico/Impacto:** Ação + Contexto + Métrica/Resultado`.
- Estruturar a seção de habilidades técnicas em categorias canônicas (Back-end & Arquitetura, Front-end & Mobile, IA & Agentes, Mensageria & Filas, Banco de Dados & ORM, DevOps & Ferramentas).
- Desenvolver o módulo `src/core/resume_formatter.py` que traduz o Markdown gerado para HTML/CSS estético com estilo de folha A4 para visualização no navegador e salvamento direto como PDF.
- Adicionar no Streamlit a opção de visualização formatada lado a lado com o Markdown puro e botão de exportação imprimível.

**Non-Goals:**
- Não gerar arquivos binários `.pdf` através de drivers pesados que exigem binários do sistema operacional (como `wkhtmltopdf` ou navegadores headless instalados no host). A geração para PDF será viabilizada via HTML imprimível com `window.print()` e `@media print` CSS padrão.

## Decisions

### 1. Gramática Rígida no Prompt do Gerador
- **Decisão**: Fornecer o template exato e exemplos de cada seção no prompt de sistema do `resume_generator`, proibindo cabeçalhos fora do padrão ou listas de habilidades sem categorização.
- **Alternativas consideradas**:
  - Pós-processar o texto via regex: Frágil e propenso a truncar dados complexos.
  - Deixar o modelo livre com poucas instruções: Gera inconsistências nos títulos e perde o padrão de tópicos de impacto nos bullets.

### 2. Conversão e Estilização HTML/CSS Própria (`resume_formatter.py`)
- **Decisão**: Criar um conversor simples de Markdown para HTML embutindo um tema CSS corporativo inspirado no documento real (fonte sem serifa limpa, destaque sutil para cargos, títulos de seções em caixa alta com borda inferior `#1f2937`, tabela de habilidades com grid estilizado).
- **Vantagem**: Funciona 100% nativo no Streamlit via `st.components.v1.html` e permite impressão direta do usuário em PDF com Ctrl+P ou botão dedicado.

### 3. Integração com o `quality_reviewer`
- **Decisão**: Atualizar a avaliação do revisor para checar não apenas alucinações, mas também se o formato seguiu o padrão de seções canônicas e bullets iniciados por negrito com tópico de impacto.

## Risks / Trade-offs

- **[Risk] Vaga com termos técnicos não mapeados nas categorias fixas** → **Mitigação**: O modelo é instruído a criar uma categoria apropriada ou encaixar na categoria mais próxima (ex: 'Dados & IA' ou 'Ferramentas Específicas').
- **[Risk] Impressão em páginas múltiplas com quebra de bloco feia** → **Mitigação**: O CSS de impressão conterá `page-break-inside: avoid;` nos blocos de cargos e projetos para não cortar uma experiência ao meio entre duas páginas.
