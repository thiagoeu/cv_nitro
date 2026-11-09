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
O sistema SHALL listar repositórios públicos concorrentemente com a análise de vaga, ranqueá-los por relevância e fornecer ao gerador, no mesmo contexto da redação, os extratos higienizados dos READMEs dos repositórios selecionados, sem chamadas adicionais ao modelo para obtê-los.

#### Scenario: Repositório correspondente encontrado
- **WHEN** a vaga exige "Python" e o usuário possui um repositório Python
- **THEN** o sistema classifica o repositório por pontuação de relevância e inclui o extrato técnico do README dele no contexto da geração do currículo

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

#### Scenario: Geração com portfólio em uma única chamada
- **WHEN** o currículo é gerado com repositórios do GitHub selecionados
- **THEN** a redação do currículo é feita em uma única chamada ao modelo, sem rodada intermediária de ferramenta

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
O sistema SHALL revisar o currículo gerado contra alucinações e conformidade de layout, classificando falhas leves para refinamento cirúrgico de seção (*delta patching*) ou falhas graves para reescrita completa. O refinamento MUST localizar a seção pelo título no idioma da vaga.

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
- **THEN** o sistema valida o currículo e gera o diagnóstico de aderência de termos utilizando apenas as regras determinísticas, sem invocar o modelo auditor, exceto pelo refinamento de seção previsto para defeitos críticos

#### Scenario: Falha de API durante a auditoria
- **WHEN** a API do auditor falhar ou exceder limites
- **THEN** o revisor não aprova silenciosamente o documento e sinaliza o erro explicitamente no estado

#### Scenario: Refinamento em currículo de vaga em inglês
- **WHEN** um currículo gerado para vaga em inglês cita uma URL de repositório que não consta no portfólio retornado pelo GitHub
- **THEN** o refinamento reescreve a seção "KEY PROJECTS" e a URL inexistente deixa de constar no currículo

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
O sistema SHALL produzir uma Carta de Apresentação (Cover Letter) altamente personalizada para a vaga, conectando a trajetória do candidato e repositórios do GitHub com os requisitos solicitados, sem atribuir ao candidato experiência nas pendências técnicas identificadas.

#### Scenario: Geração de Cover Letter com sucesso
- **WHEN** o processo de otimização de currículo é concluído
- **THEN** o sistema disponibiliza a Cover Letter no mesmo idioma da vaga, destacando fit cultural e técnico

#### Scenario: Vaga com pendências técnicas
- **WHEN** a vaga exige tecnologias classificadas como pendências técnicas
- **THEN** a carta pode citá-las apenas como interesse ou disposição para aprender, nunca como experiência do candidato

#### Scenario: Carta com marcador não preenchido
- **WHEN** a carta gerada contém um marcador no formato `<...>` que não é um endereço de e-mail
- **THEN** a carta é salva e o usuário vê um aviso indicando que ela precisa de revisão manual

### Requirement: Sanitização de saída HTML do currículo
O sistema SHALL sanitizar e escapar caracteres especiais HTML (XSS prevention) em todo o conteúdo gerado antes da renderização e exportação.

#### Scenario: Conteúdo contendo tags maliciosas
- **WHEN** o currículo base ou descrição da vaga contiver tags HTML ou scripts injetados
- **THEN** o formatador escapa os caracteres perigosos impedindo a execução de scripts no navegador

### Requirement: Falhas do modelo visíveis ao usuário
O sistema SHALL informar ao usuário quando uma chamada ao modelo de IA ou a consulta ao GitHub falhar e MUST NOT salvar no histórico um currículo ou carta de fallback como se fosse resultado otimizado.

#### Scenario: Falha na análise da vaga ou na geração do currículo
- **WHEN** a chamada ao modelo falha na análise da vaga ou na geração do currículo
- **THEN** o usuário vê a mensagem de erro e nenhuma candidatura é salva no histórico

#### Scenario: Falha na revisão ou na carta de apresentação
- **WHEN** a chamada ao modelo falha no revisor ou no gerador de carta
- **THEN** o currículo gerado é salvo e o usuário vê um aviso descrevendo a etapa que falhou
- **AND** nenhuma carta genérica de fallback é exibida ou salva

#### Scenario: Avisos de várias etapas na mesma execução
- **WHEN** a consulta ao GitHub e a geração da carta falham na mesma otimização
- **THEN** a tela da candidatura exibe os dois avisos, inclusive ao ser reaberta depois

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
O sistema SHALL permitir a execução configurável do pipeline multi-agente, possibilitando ativar ou desativar etapas opcionais para redução no consumo de tokens e tempo de resposta, sem deixar de corrigir defeitos críticos detectados por validação determinística.

#### Scenario: Execução em modo econômico sem carta de apresentação
- **WHEN** o usuário desmarca a geração de Cover Letter nas opções da otimização
- **THEN** o pipeline ignora o nó de geração de carta e consome tokens apenas para o currículo e diagnóstico

#### Scenario: Execução com revisão simplificada
- **WHEN** o usuário ativa o modo econômico de tokens
- **THEN** o sistema executa prompts enxutos de resumo de contexto e limita loops de refinamento da LLM

#### Scenario: Defeito crítico no modo econômico
- **WHEN** no modo econômico a validação determinística encontra um marcador não preenchido ou uma URL de repositório fora do portfólio dentro de uma seção identificável
- **THEN** o sistema executa um único refinamento dessa seção sem acionar o revisor por modelo e registra no diagnóstico os problemas que restarem

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
O sistema SHALL classificar previamente os requisitos da vaga contra o perfil e portfólio do candidato em tecnologias comprovadas (diretas ou equivalentes) e pendências técnicas reais, proibindo estritamente a inserção de pendências técnicas na tabela de habilidades ou experiências profissionais do currículo gerado. A classificação MUST usar a mesma base de evidências fornecida ao gerador e MUST NOT tratar tecnologias irmãs de uma mesma família como equivalentes.

#### Scenario: Vaga com requisitos não comprovados pelo histórico
- **WHEN** a vaga exige tecnologias ausentes no currículo base e no portfólio do candidato (como C# ou .NET para perfil Node/React)
- **THEN** o sistema classifica esses termos estritamente como pendências técnicas e proíbe o gerador de atribuí-los às experiências profissionais ou à tabela de habilidades

#### Scenario: Uso exclusivo de repositórios comprovados em projetos
- **WHEN** a seção de projetos em destaque é redigida
- **THEN** o gerador utiliza exclusivamente os repositórios selecionados no portfólio comprovado do GitHub com suas respectivas URLs

#### Scenario: Tecnologia específica exigida e candidato com uma irmã
- **WHEN** a vaga exige PostgreSQL e o candidato comprova apenas MySQL
- **THEN** PostgreSQL é classificado como pendência técnica
- **AND** um requisito genérico como SQL continua comprovado por MySQL

#### Scenario: Evidência presente apenas no README de um repositório selecionado
- **WHEN** a vaga exige Redis, o currículo base não cita Redis e o README de um dos repositórios selecionados descreve o uso de Redis
- **THEN** Redis é classificado como tecnologia comprovada
- **AND** a menção a Redis na seção de projetos não é tratada como violação da trava factual

#### Scenario: Termo técnico curto e ambíguo
- **WHEN** a vaga exige C, R ou Go e o currículo do candidato cita apenas C#, C++, "R&D" ou "go-live"
- **THEN** o requisito é classificado como pendência técnica e não como tecnologia comprovada

### Requirement: Tempo máximo das chamadas de modelo
O sistema SHALL limitar cada tentativa de chamada a um modelo a 120 segundos, com no máximo uma nova tentativa por modelo antes de passar ao modelo de reserva, e MUST encerrar a otimização com erro visível quando todos os modelos falharem.

#### Scenario: Modelo principal sem resposta
- **WHEN** o modelo principal não responde dentro do limite de tempo
- **THEN** o sistema passa para o próximo modelo de reserva configurado

#### Scenario: Todos os modelos indisponíveis
- **WHEN** o modelo principal e todos os modelos de reserva falham
- **THEN** o usuário vê uma mensagem de erro e nenhuma candidatura é salva

### Requirement: Corrigir a seção onde está o defeito crítico
O sistema SHALL direcionar o refinamento de seção para a seção do currículo que contém o defeito crítico detectado pela validação determinística (marcador não preenchido, URL de repositório fora do portfólio ou pendência técnica atribuída ao candidato). Quando o defeito estiver fora de qualquer seção, como no título do cargo, o modo rígido MUST regenerar o currículo inteiro.

#### Scenario: Pendência técnica no resumo profissional
- **WHEN** o currículo gerado atribui ao candidato uma pendência técnica dentro da seção de resumo profissional
- **THEN** o refinamento reescreve a seção de resumo profissional, e não a de habilidades técnicas

#### Scenario: Pendência técnica no título do cargo em modo rígido
- **WHEN** em modo rígido o currículo gerado cita uma pendência técnica no título do cargo, antes da primeira seção
- **THEN** o sistema regenera o currículo completo com o feedback do defeito

### Requirement: Não aprovar currículo com defeito crítico remanescente
O sistema MUST NOT marcar como aprovado um currículo cuja versão final ainda contenha defeito crítico da validação determinística, em modo rígido ou econômico. O currículo é salvo e o usuário vê um aviso que descreve os defeitos que restaram.

#### Scenario: Defeito não corrigido no modo econômico
- **WHEN** no modo econômico o refinamento de seção não remove a pendência técnica atribuída ao candidato
- **THEN** a candidatura é salva sem a marcação de aprovada
- **AND** a tela da candidatura exibe um aviso citando a pendência técnica, inclusive ao ser reaberta depois

#### Scenario: Limite de tentativas atingido com melhor versão válida
- **WHEN** em modo rígido o limite de tentativas é atingido e uma versão anterior sem defeitos críticos foi registrada
- **THEN** o sistema salva essa versão anterior e nenhum aviso de defeito crítico é exibido

### Requirement: Detectar currículo vazio ou truncado
O sistema SHALL tratar como defeito crítico um currículo gerado vazio ou cuja geração tenha sido interrompida pelo limite de saída do modelo.

#### Scenario: Resposta vazia do gerador em modo econômico
- **WHEN** o gerador retorna texto vazio e a revisão está em modo econômico
- **THEN** a candidatura não é marcada como aprovada e o usuário vê um aviso de currículo vazio

#### Scenario: Saída interrompida pelo limite de tokens
- **WHEN** o modelo encerra a geração do currículo por atingir o limite de saída
- **THEN** a validação determinística registra o defeito crítico de currículo truncado

### Requirement: Conferir a seção indicada pelo revisor por modelo
O sistema SHALL conferir a seção que o revisor por modelo indicar para refinamento com os títulos existentes no currículo, aceitando o nome da seção em qualquer um dos idiomas suportados. Quando a seção não existir no currículo, o sistema MUST regenerar o currículo em vez de executar um refinamento que não altera o documento.

#### Scenario: Seção indicada em outro idioma
- **WHEN** o currículo está em inglês e o revisor indica "HABILIDADES TÉCNICAS" para refinamento
- **THEN** o refinamento é aplicado à seção "TECHNICAL SKILLS"

#### Scenario: Seção inexistente no currículo
- **WHEN** o revisor indica para refinamento uma seção que não corresponde a nenhum título do currículo
- **THEN** o sistema regenera o currículo completo com o feedback do revisor

### Requirement: Incremento sob demanda de projetos em destaque via link do GitHub
O sistema SHALL permitir que o usuário adicione incrementalmente novos projetos à seção de projetos do currículo gerado fornecendo links de repositórios do GitHub, buscando os dados do repositório e redigindo cada entrada via IA no idioma e padrão canônico do documento sem sobrescrever os projetos existentes.

#### Scenario: Adição incremental de projeto por link do GitHub
- **WHEN** o usuário informa um link válido de repositório do GitHub na seção de incremento de projetos do currículo e aciona a adição
- **THEN** o sistema coleta os metadados e o README do repositório, gera a descrição formatada no idioma e padrão do documento (título H3, stack em itálico, bullets em 1ª pessoa e link do repositório) e anexa o projeto ao final da seção de projetos mantendo os anteriores intactos

#### Scenario: Adição sucessiva de múltiplos projetos e prevenção de duplicidade
- **WHEN** o usuário envia um novo link de repositório posteriormente ou informa um link já presente na seção de projetos
- **THEN** o sistema preserva todos os projetos existentes, adiciona apenas os novos projetos (ou atualiza o projeto de mesma URL sem duplicá-lo) e recompila a folha A4 automaticamente

#### Scenario: Tratamento de link inválido ou repositório inacessível
- **WHEN** o usuário informa uma URL que não pertence a um repositório válido do GitHub ou a consulta à API falha
- **THEN** o sistema exibe uma mensagem de erro clara ao usuário e preserva o currículo atual sem alterações

### Requirement: Otimizar currículo geral sem vaga específica por endpoint independente
O sistema SHALL disponibilizar um botão e endpoint independentes para gerar um currículo geral de alto impacto sem exigir vaga específica, mantendo o fluxo principal inalterado. O endpoint geral MUST exigir apenas o currículo base, enriquecer opcionalmente o documento com repositórios do GitHub, destacar as tecnologias comprovadas e salvar o resultado em Candidaturas com visualização A4.

#### Scenario: Geração de currículo geral apenas com currículo base
- **WHEN** o usuário informa o currículo base (deixando título e descrição da vaga em branco) e aciona o botão de otimização geral sem vaga específica
- **THEN** o sistema executa o endpoint dedicado de otimização geral (sem acionar o grafo de análise de vaga específica), gera o currículo estruturado no padrão A4 destacando as tecnologias relevantes do candidato, registra o título padrão (ou o foco profissional informado) e redireciona para a tela da candidatura gerada

#### Scenario: Geração de currículo geral enriquecida com portfólio do GitHub
- **WHEN** o usuário informa o currículo base e um nome de usuário do GitHub ao acionar o botão de otimização geral
- **THEN** o sistema consulta os repositórios públicos não-fork do usuário, seleciona os principais projetos pelo mérito técnico e estrelas, extrai seus READMEs higienizados e inclui a seção de Projetos em Destaque e as tecnologias comprovadas no currículo geral gerado

#### Scenario: Validação de currículo base ausente no modo geral
- **WHEN** o usuário aciona o botão de otimização geral sem ter preenchido ou enviado o currículo base
- **THEN** o sistema exibe erro informando que o currículo base é obrigatório e não inicia chamadas aos modelos de IA

#### Scenario: Isolamento em relação ao fluxo principal de vaga específica
- **WHEN** o usuário utiliza o botão original de otimização para vaga específica ou o novo botão de otimização geral
- **THEN** cada botão aciona seu respectivo endpoint sem interferir nos prompts, regras ou estado do outro fluxo

#### Scenario: Edição e adição de projetos escolhidos pelo usuário no currículo geral
- **WHEN** o currículo geral sem vaga específica é gerado e aberto (ou quando o usuário informa links de projetos específicos do GitHub)
- **THEN** o usuário dispõe do botão/aba de edição do currículo e da seção de adicionar projetos por link do GitHub para incluir ou editar quantos projetos desejar mantendo o padrão do documento A4

