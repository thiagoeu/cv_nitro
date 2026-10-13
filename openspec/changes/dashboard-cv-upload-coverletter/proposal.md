# Proposal: Suporte a Upload (PDF/DOCX), Geração Multilíngue, Cover Letter e Dashboard de Vagas

## Why

Atualmente, o GitMatch exige que o usuário copie e cole manualmente o conteúdo de seu currículo em formato Markdown e gera apenas o currículo ajustado no idioma padrão. Na prática profissional, a maioria dos usuários mantém seus currículos em arquivos PDF ou DOCX, candidata-se a vagas internacionais que exigem tanto o currículo quanto a Carta de Apresentação (Cover Letter) em inglês, e precisa acompanhar o histórico de candidaturas através de um painel visual consolidado (com links das vagas e datas) para gerenciar o funil de aplicações.

## What Changes

- **Upload de Arquivos de Currículo**: Adiciona suporte a upload de arquivos nos formatos `.pdf`, `.docx` e `.md`, extraindo o texto de forma limpa para processamento pelos agentes, mantendo fallback para inserção direta de texto.
- **Detecção e Geração Multilíngue**: O `job_analyzer` detecta automaticamente o idioma da descrição da vaga (por exemplo, inglês ou português), e o gerador produz o currículo otimizado no mesmo idioma exigido pela vaga.
- **Geração de Cover Letter (Carta de Apresentação)**: Novo nó no fluxo de agentes ou extensão do gerador para produzir uma Carta de Apresentação altamente personalizada, cruzando os requisitos da vaga com os projetos do GitHub e o currículo do candidato.
- **Armazenamento e Histórico Enriquecido**: O `history_manager` passa a registrar opcionalmente o link da vaga (URL), idioma detectado, data da geração, status e a respectiva Cover Letter gerada.
- **Dashboard Inicial de Aplicações**: A página inicial do Streamlit passa a exibir um painel gerencial interativo com métricas (total de aplicações, tecnologias mais demandadas, histórico temporal) e uma tabela com a vaga, link clicável, data do ajuste e ações de visualização/download.

## Capabilities

### New Capabilities
- `application-dashboard`: Painel gerencial e analítico com métricas, gráficos das tecnologias aplicadas e tabela consolidada de candidaturas e links para acompanhamento das vagas.

### Modified Capabilities
- `resume-optimization`: Passa a aceitar entrada de currículo via upload (PDF, DOCX, Markdown), adapta o idioma de saída conforme o idioma da vaga (ex: inglês) e gera Cover Letter complementar aos projetos do GitHub.
- `resume-history`: Atualiza a estrutura de metadados para persistir a URL da vaga, a Cover Letter gerada e permitir consumo dos dados pelo dashboard analítico.

## Impact

- **Código Afetado**:
  - `src/agents/state.py`: inclusão de campos para URL da vaga, idioma da vaga e `generated_cover_letter_md`.
  - `src/agents/nodes.py`: suporte a detecção de idioma, geração de Cover Letter e compatibilidade multilíngue.
  - `src/agents/graph.py`: orquestração do novo fluxo/nó de geração de Cover Letter.
  - `src/core/history_manager.py`: suporte a novos metadados (URL, cover letter).
  - `src/core/document_parser.py` (novo): utilitário para extração de texto de PDF, DOCX e MD.
  - `app.py`: reformulação da interface para incluir o Dashboard na home, abas/seção de nova candidatura com upload de arquivos e abas de resultado (Currículo + Cover Letter).
- **Dependências**:
  - `pypdf` para leitura de PDFs.
  - `python-docx` para leitura de DOCX.
