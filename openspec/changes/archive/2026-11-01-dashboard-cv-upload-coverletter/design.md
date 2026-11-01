# Design: Suporte a Upload, Geração Multilíngue, Cover Letter e Dashboard de Vagas

## Context

Atualmente o GitMatch opera com entrada de currículo exclusivamente via caixa de texto em Markdown e gera apenas o currículo otimizado. As candidaturas geradas são salvas em arquivos locais `.md` na pasta `history/`, com um frontmatter simples em comentário HTML. Para atender às necessidades reais de busca de emprego em vagas nacionais e internacionais, o sistema precisa aceitar currículos pré-existentes em PDF/DOCX, respeitar o idioma da vaga (gerando currículo e Cover Letter em inglês ou português) e oferecer um painel visual consolidado na página inicial para rastreamento de aplicações com suas respectivas URLs e datas.

## Goals / Non-Goals

**Goals:**
- Permitir upload de currículos em formatos `.pdf`, `.docx`, `.md` e `.txt` com extração limpa de texto.
- Detectar automaticamente o idioma da vaga no `job_analyzer` e instruir os agentes geradores a redigir o currículo na mesma língua.
- Adicionar a capacidade de gerar uma Carta de Apresentação (Cover Letter) profissional e personalizada orientada a ATS e fit cultural.
- Enriquecer o `history_manager` para registrar a URL da vaga, idioma e a Cover Letter junto ao currículo.
- Reformular a interface no Streamlit com uma experiência centrada em Dashboard na página inicial, exibindo métricas, gráficos das tecnologias e tabela de vagas aplicadas com links e datas.

**Non-Goals:**
- Não incluir autenticação multiusuário (o app continua operando em modo local desktop/single-user).
- Não realizar scraping automático de páginas de vagas a partir do link (o link da vaga é puramente para referência cadastral do usuário).
- Não substituir o motor de LLM (permanece com Google Gemini via `langchain-google-genai`).

## Decisions

### 1. Extração de Documentos via `pypdf` e `python-docx`
- **Decisão**: Utilizar `pypdf` para extração de texto de PDFs e `python-docx` para DOCX em um módulo isolado `src/core/document_parser.py`.
- **Alternativas consideradas**:
  - `pdfplumber` / `tesseract`: mais pesados e lentos para currículos padrão baseados em texto.
  - LLM multimodal direto para ler o PDF: gastaria tokens desnecessários da API para uma tarefa puramente textual.
- **Vantagem**: Bibliotecas puramente Python, rápidas, estáveis no Windows e sem dependências de binários nativos complexos.

### 2. Detecção de Idioma pelo `job_analyzer`
- **Decisão**: Expandir o esquema Pydantic `JobAnalysis` no `job_analyzer` para incluir o campo `language: str` (ex: "en", "pt", "es").
- **Alternativas consideradas**:
  - Biblioteca `langdetect`: adicionaria mais uma dependência com heurísticas que falham em descrições de vagas curtas ou com termos mistos de TI.
  - LLM já analisa a vaga no nó inicial sem custo extra de requisição.

### 3. Integração do Nó `cover_letter_generator` no Grafo
- **Decisão**: Incluir um novo nó `cover_letter_generator` executado após o `quality_reviewer` (ou em encadeamento final antes do END) que recebe o estado aprovado e constrói a carta formal no idioma da vaga.
- **Alternativas consideradas**:
  - Gerar o currículo e a cover letter em um único prompt: gera respostas muito longas que aumentam a chance de truncamento ou perda de qualidade nas diretrizes ATS de cada documento.

### 4. Armazenamento Unificado no Histórico
- **Decisão**: Manter o padrão de arquivos no diretório `history/`, estendendo o JSON de metadados com `job_url`, `language` e `has_cover_letter`, separando o currículo da cover letter por um delimitador claro (`<!-- COVER_LETTER -->`).
- **Alternativas consideradas**:
  - Banco SQLite: adicionaria complexidade de migração desnecessária para o volume local atual.

### 5. Layout do Dashboard no Streamlit
- **Decisão**: Apresentar na home abas claras (`📊 Dashboard de Aplicações` e `🚀 Nova Otimização`). No Dashboard:
  - Cards de métricas rápidas (Total de candidaturas, Vagas por idioma).
  - Gráfico de barras com as tecnologias mais frequentes nas vagas aplicadas (extraídas do histórico).
  - Tabela com `Vaga`, `Link` (clicável), `Data/Hora` e botão para carregar e inspecionar a candidatura no visualizador com abas (Currículo e Carta).

## Risks / Trade-offs

- **[Risk] PDFs diagramados ou com colunas duplas complexas** → **Mitigação**: `pypdf` extrai o texto sequencialmente. Caso o texto venha desordenado, o usuário ainda tem a opção de inspecionar/editar o texto na interface antes do envio ao grafo.
- **[Risk] Vaga bilíngue (ex: título em português com requisitos em inglês)** → **Mitigação**: O prompt do LLM é instruído a priorizar o idioma em que a maior parte das exigências e responsabilidades está redigida.
- **[Risk] Compatibilidade com histórico antigo** → **Mitigação**: O `history_manager` terá leitura retrocompatível com arquivos `.md` antigos que não possuam `job_url` ou Cover Letter.
