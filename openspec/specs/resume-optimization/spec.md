# resume-optimization Specification

## Purpose
Otimiza currículos automaticamente cruzando vagas com repositórios do GitHub através de um fluxo de IA multi-agente.

## Requirements

### Requirement: Analisar descrição da vaga
O sistema SHALL extrair os requisitos, tecnologias e soft skills a partir de uma descrição de vaga fornecida pelo usuário.

#### Scenario: Vaga com requisitos claros
- **WHEN** uma vaga de "Desenvolvedor Python" é fornecida em texto
- **THEN** o sistema extrai "Python" e tecnologias relacionadas como requisitos

### Requirement: Buscar evidências no GitHub
O sistema SHALL listar repositórios públicos concorrentemente com a análise de vaga e permitir a obtenção detalhada de arquivos README sob demanda através de chamada de ferramenta (*tool-calling*) pelo gerador.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema classifica o repositório por pontuação de relevância e disponibiliza o extrato técnico sob demanda

#### Scenario: Repositórios ranqueados por relevância
- **WHEN** o usuário possui múltiplos repositórios públicos
- **THEN** o sistema ignora forks e seleciona com prioridade os projetos cujas linguagens, tópicos e descrições apresentem maior pontuação de correspondência com as tecnologias da vaga

#### Scenario: Falha de comunicação ou limite de requisições da API
- **WHEN** a API do GitHub retornar erro HTTP (ex: 403 por rate limit, 404 por usuário inexistente ou timeout)
- **THEN** o sistema registra a mensagem de falha na lista de erros do estado sem interromper a execução dos demais agentes

#### Scenario: Usuário com formato inválido
- **WHEN** o nome de usuário fornecido contém caracteres especiais inválidos ou tentativas de injeção
- **THEN** o sistema rejeita a chamada de rede e retorna lista vazia de repositórios de forma segura

#### Scenario: Timeout ou instabilidade na API externa
- **WHEN** a API do GitHub demorar mais que o tempo limite configurado (timeout)
- **THEN** o sistema aborta a requisição sem bloquear indefinidamente a aplicação

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

### Requirement: Revisar currículo gerado
O sistema SHALL revisar o currículo gerado contra alucinações e conformidade de layout, classificando falhas leves para refinamento cirúrgico de seção (*delta patching*) ou falhas graves para reescrita completa.

#### Scenario: Identificação de alucinação ou ajuste de seção
- **WHEN** o currículo gerado apresenta erro pontual de formatação ou de alinhamento em uma seção específica
- **THEN** o sistema aciona o refinamento cirúrgico da seção afetada sem reescrever o restante do documento

#### Scenario: Identificação de alucinação
- **WHEN** o currículo gerado cita uma ferramenta que não está no currículo original nem no GitHub
- **THEN** o revisor rejeita o currículo e solicita correção ao gerador

#### Scenario: Verificação determinística de integridade
- **WHEN** o currículo gerado contiver links de repositórios que não constam na lista obtida do GitHub ou estrutura de tabela fora do padrão
- **THEN** o revisor rejeita o currículo gerado e emite feedback corretivo imediato sem gastar chamadas de LLM

#### Scenario: Revisão em modo econômico
- **WHEN** a execução estiver configurada em modo econômico (`strict_review=False`)
- **THEN** o sistema valida o currículo e gera o diagnóstico de aderência de termos utilizando apenas as regras determinísticas, sem invocar o modelo auditor

#### Scenario: Falha de API durante a auditoria
- **WHEN** a API do auditor falhar ou exceder limites
- **THEN** o revisor não aprova silenciosamente o documento e sinaliza o erro explicitamente no estado

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

### Requirement: Sanitização de saída HTML do currículo
O sistema SHALL sanitizar e escapar caracteres especiais HTML (XSS prevention) em todo o conteúdo gerado antes da renderização e exportação.

#### Scenario: Conteúdo contendo tags maliciosas
- **WHEN** o currículo base ou descrição da vaga contiver tags HTML ou scripts injetados
- **THEN** o formatador escapa os caracteres perigosos impedindo a execução de scripts no navegador

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

### Requirement: Controle modular de etapas e economia de tokens
O sistema SHALL permitir a execução configurável do pipeline multi-agente, possibilitando ativar ou desativar etapas opcionais para redução no consumo de tokens e tempo de resposta.

#### Scenario: Execução em modo econômico sem carta de apresentação
- **WHEN** o usuário desmarca a geração de Cover Letter nas opções da otimização
- **THEN** o pipeline ignora o nó de geração de carta e consome tokens apenas para o currículo e diagnóstico

#### Scenario: Execução com revisão simplificada
- **WHEN** o usuário ativa o modo econômico de tokens
- **THEN** o sistema executa prompts enxutos de resumo de contexto e limita loops de refinamento da LLM

### Requirement: Higienizar e filtrar conteúdo de READMEs
O sistema SHALL remover elementos visuais e metadados irrelevantes de READMEs (como badges, imagens e seções triviais de licença) e fornecer um extrato técnico estruturado com limite controlado de caracteres para o gerador de currículo e carta de apresentação.

#### Scenario: Extração limpa de contexto técnico
- **WHEN** um repositório contém badges, imagens e texto longo de instalação em seu README
- **THEN** o sistema filtra esses blocos e envia ao modelo apenas a descrição do projeto, funcionalidades e stack técnica respeitando o teto de caracteres definido

### Requirement: Execução concorrente inicial no grafo
O sistema SHALL disparar a análise textual da vaga e a consulta à API de repositórios do GitHub concorrentemente a partir do nó inicial do grafo, sincronizando os resultados em um nó determinístico de ranqueamento de relevância.

#### Scenario: Disparo simultâneo de nós iniciais
- **WHEN** o grafo é iniciado com os dados da vaga e o nome de usuário do GitHub
- **THEN** as requisições de análise de requisitos e de listagem de repositórios são executadas em paralelo

### Requirement: Preservar melhor versão e interromper revisão por estagnação
O sistema SHALL manter um snapshot da versão de currículo com a maior pontuação ATS durante o ciclo de revisão, interrompendo novas rodadas caso uma revisão não supere a melhor nota anterior e restaurando automaticamente a versão de maior pontuação.

#### Scenario: Revisão subsequente com nota inferior ou igual à anterior
- **WHEN** uma segunda rodada de avaliação do revisor resulta em pontuação ATS menor ou igual à melhor nota já registrada e sem erros estruturais determinísticos críticos
- **THEN** o sistema encerra o loop de revisão imediatamente para não forçar alucinações e restaura o currículo e o diagnóstico correspondentes à melhor versão avaliada

#### Scenario: Revisão subsequente que melhora a pontuação
- **WHEN** uma rodada de refinamento eleva a pontuação ATS acima da tentativa anterior
- **THEN** o sistema atualiza o snapshot da melhor versão com o novo currículo e diagnóstico aprimorados

### Requirement: Obter arquivos README selecionados de forma concorrente
O sistema SHALL realizar o download dos arquivos README dos repositórios selecionados no ranking de relevância de maneira paralela.

#### Scenario: Download concorrente dos Top 3 READMEs
- **WHEN** o nó de ranqueamento seleciona múltiplos repositórios relevantes do candidato
- **THEN** as requisições para obtenção dos conteúdos de README são disparadas concorrentemente respeitando o tempo limite configurado

### Requirement: Mapear competências comprovadas e isolar pendências técnicas
O sistema SHALL classificar previamente os requisitos da vaga contra o perfil e portfólio do candidato em tecnologias comprovadas (diretas ou equivalentes) e pendências técnicas reais, proibindo estritamente a inserção de pendências técnicas na tabela de habilidades ou experiências profissionais do currículo gerado.

#### Scenario: Vaga com requisitos não comprovados pelo histórico
- **WHEN** a vaga exige tecnologias ausentes no currículo base e no portfólio do candidato (como C# ou .NET para perfil Node/React)
- **THEN** o sistema classifica esses termos estritamente como pendências técnicas e proíbe o gerador de atribuí-los às experiências profissionais ou à tabela de habilidades

#### Scenario: Uso exclusivo de repositórios comprovados em projetos
- **WHEN** a seção de projetos em destaque é redigida
- **THEN** o gerador utiliza exclusivamente os repositórios selecionados no portfólio comprovado do GitHub com suas respectivas URLs
