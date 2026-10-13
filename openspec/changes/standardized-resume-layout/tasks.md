# Tasks

## 1. Padronização dos Prompts dos Agentes

- [x] 1.1 Atualizar o prompt do `resume_generator` em `src/agents/nodes.py` com o template canônico de alta fidelidade (Header com contatos em linha única, Resumo denso, Tabela de Habilidades categorizada, bullets de experiência no padrão `● **Tópico/Impacto:** Ação + Contexto + Resultado`, Projetos com stack e link GitHub, Formação, Certificações e Idiomas), verificando formatação esperada
- [x] 1.2 Atualizar as instruções do `quality_reviewer` em `src/agents/nodes.py` para auditar a presença das seções canônicas e o padrão dos bullet points

## 2. Formatador Visual e Módulo de Exportação HTML/PDF

- [x] 2.1 Criar `src/core/resume_formatter.py` contendo a função `format_resume_to_html(markdown_content, title)` com folha de estilo A4 profissional, tipografia limpa, bordas sutis e regras de `@media print` para salvamento direto como PDF
- [x] 2.2 Criar `tests/test_resume_formatter.py` verificando a conversão de Markdown para HTML estruturado e conferindo presença dos estilos de impressão e classes visuais

## 3. Integração na Interface Streamlit

- [x] 3.1 Atualizar `app.py` para incluir a aba 'Visualização em Folha (A4)' e botão de download do HTML imprimível / PDF nas telas de resultado e histórico, mantendo a opção de Markdown puro

## 4. Verificação e Integração Ponta a Ponta

- [x] 4.1 Executar suíte completa de testes (`tests/`) e validar via AppTest a renderização visual do currículo formatado no Streamlit
