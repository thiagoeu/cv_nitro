# Spec Delta

## MODIFIED Requirements

### Requirement: Gerar currículo otimizado
O sistema SHALL gerar um currículo no formato Markdown incluindo uma seção de "Projetos em Destaque" baseada nas evidências extraídas do GitHub, escrito inteiramente no idioma detectado da vaga (português, inglês ou espanhol), traduzindo o conteúdo do currículo base quando ele estiver em outro idioma.

#### Scenario: Currículo gerado com sucesso
- **WHEN** os metadados do GitHub e os requisitos da vaga estão alinhados
- **THEN** um documento Markdown com o currículo ajustado é retornado

#### Scenario: Vaga em inglês com currículo base em português
- **WHEN** a vaga está em inglês e o currículo base está em português
- **THEN** o currículo gerado está todo em inglês, incluindo títulos de seção, cabeçalho e categorias da tabela de habilidades, tópicos dos bullets, cargos, formação, certificações e idiomas
- **AND** nomes de empresas, projetos e tecnologias permanecem como no original

#### Scenario: Carta de apresentação no idioma da vaga
- **WHEN** a vaga está em inglês ou espanhol
- **THEN** a carta de apresentação é escrita no mesmo idioma da vaga

## ADDED Requirements

### Requirement: Falhas do modelo visíveis ao usuário
O sistema SHALL informar ao usuário quando uma chamada ao modelo de IA falhar e MUST NOT salvar no histórico um currículo ou carta de fallback como se fosse resultado otimizado.

#### Scenario: Falha na análise da vaga ou na geração do currículo
- **WHEN** a chamada ao modelo falha na análise da vaga ou na geração do currículo
- **THEN** o usuário vê a mensagem de erro e nenhuma candidatura é salva no histórico

#### Scenario: Falha na revisão ou na carta de apresentação
- **WHEN** a chamada ao modelo falha no revisor ou no gerador de carta
- **THEN** o currículo gerado é salvo e o usuário vê um aviso descrevendo a etapa que falhou
- **AND** nenhuma carta genérica de fallback é exibida ou salva

### Requirement: Preservar estrutura do currículo enviado
O sistema SHALL extrair o texto de currículos DOCX na ordem em que parágrafos e tabelas aparecem no documento, representando linhas de tabela como linhas de tabela Markdown.

#### Scenario: DOCX com tabela de habilidades no meio do documento
- **WHEN** o usuário envia um DOCX com a tabela de habilidades logo abaixo do título "HABILIDADES TÉCNICAS"
- **THEN** o texto extraído contém as linhas da tabela imediatamente após esse título, no formato `| Categoria | Tecnologias |`

### Requirement: Tabela de habilidades renderizada como tabela
O sistema SHALL renderizar a tabela Markdown de habilidades como tabela na visualização A4, usando a linha separadora para identificar o cabeçalho, independentemente do idioma.

#### Scenario: Tabela com cabeçalho em inglês
- **WHEN** o currículo contém uma tabela com cabeçalho `| Category | Technologies |` seguido de `| :--- | :--- |`
- **THEN** a primeira linha é exibida como cabeçalho da tabela e as demais como células

#### Scenario: Linha com "GitHub" fora do cabeçalho
- **WHEN** uma linha após a primeira seção contém "|" e a palavra "GitHub"
- **THEN** ela não é exibida como barra de contatos
