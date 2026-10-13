# Spec Delta

## ADDED Requirements

### Requirement: Suporte a upload de currículo em múltiplos formatos
O sistema SHALL permitir o carregamento do currículo base através de upload de arquivos nos formatos PDF, DOCX ou Markdown, extraindo o conteúdo de texto para envio ao grafo de agentes.

#### Scenario: Upload de arquivo PDF ou DOCX válido
- **WHEN** o usuário seleciona um arquivo PDF ou DOCX no campo de upload
- **THEN** o sistema extrai o texto do documento e o utiliza como currículo base para a otimização

#### Scenario: Falha ou arquivo inválido
- **WHEN** o usuário envia um arquivo corrompido ou formato não suportado
- **THEN** o sistema notifica o usuário com mensagem de erro clara e mantém a opção de colar texto manual

### Requirement: Geração de currículo no idioma da vaga
O sistema SHALL identificar automaticamente o idioma da descrição da vaga (por exemplo, inglês ou português) e produzir o currículo otimizado no mesmo idioma identificado.

#### Scenario: Vaga em inglês
- **WHEN** a descrição da vaga está redigida em inglês
- **THEN** o currículo otimizado gerado é redigido integralmente em inglês, inclusive títulos de seções e termos técnicos

#### Scenario: Vaga em português
- **WHEN** a descrição da vaga está redigida em português
- **THEN** o currículo otimizado gerado é redigido integralmente em português

### Requirement: Geração de Cover Letter personalizada
O sistema SHALL produzir uma Carta de Apresentação (Cover Letter) altamente personalizada para a vaga, conectando a trajetória do candidato e repositórios do GitHub com os requisitos solicitados.

#### Scenario: Geração de Cover Letter com sucesso
- **WHEN** o processo de otimização de currículo é concluído
- **THEN** o sistema disponibiliza a Cover Letter no mesmo idioma da vaga, destacando fit cultural e técnico
