# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
