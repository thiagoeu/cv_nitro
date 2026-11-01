# Tasks

## 1. Dependências e Parsing de Documentos

- [x] 1.1 Adicionar `pypdf` e `python-docx` ao requirements.txt e instalar no ambiente virtual, verificando instalação com import via script de teste
- [x] 1.2 Criar `src/core/document_parser.py` com suporte à extração de texto limpo para arquivos `.pdf`, `.docx`, `.md` e `.txt`, verificando testes unitários de leitura

## 2. Adaptação do Grafo de Agentes (Multilíngue e Cover Letter)

- [x] 2.1 Atualizar `GraphState` em `src/agents/state.py` adicionando os campos `job_url`, `job_language` e `generated_cover_letter_md`, verificando tipagem
- [x] 2.2 Atualizar `job_analyzer` em `src/agents/nodes.py` para detectar o idioma da descrição da vaga (`pt`, `en`, etc.) no modelo estruturado
- [x] 2.3 Atualizar `resume_generator` em `src/agents/nodes.py` para redigir o currículo integralmente no idioma identificado da vaga (ex: inglês quando a vaga for em inglês)
- [x] 2.4 Criar o nó `cover_letter_generator` em `src/agents/nodes.py` e conectá-lo na orquestração de `src/agents/graph.py`, verificando execução com mock/teste

## 3. Enriquecimento do Histórico de Aplicações

- [x] 3.1 Atualizar `src/core/history_manager.py` para persistir e carregar `job_url`, idioma e conteúdo da Cover Letter junto ao currículo, mantendo compatibilidade com registros existentes no diretório `history/`

## 4. Dashboard e Interface Streamlit

- [x] 4.1 Implementar painel de Dashboard na tela inicial de `app.py` com indicadores de volume de candidaturas, distribuição de tecnologias e tabela interativa contendo Vaga, Link clicável da vaga, Data do ajuste e Ações
- [x] 4.2 Integrar componente `st.file_uploader` para carregar arquivos PDF, DOCX e Markdown no formulário de nova candidatura, populando o currículo base e adicionando campo para URL da vaga
- [x] 4.3 Adicionar exibição com abas no Streamlit para visualizar e fazer download tanto do Currículo Otimizado quanto da Carta de Apresentação (Cover Letter)

## 5. Verificação e Integração

- [x] 5.1 Executar suíte de testes em `tests/` e validar o fluxo ponta a ponta gerando uma vaga de teste em inglês e conferindo persistência no Dashboard
