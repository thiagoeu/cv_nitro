# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Tempo máximo das chamadas de modelo
O sistema SHALL limitar cada tentativa de chamada a um modelo a 120 segundos, com no máximo uma nova tentativa por modelo antes de passar ao modelo de reserva, e MUST encerrar a otimização com erro visível quando todos os modelos falharem.

#### Scenario: Modelo principal sem resposta
- **WHEN** o modelo principal não responde dentro do limite de tempo
- **THEN** o sistema passa para o próximo modelo de reserva configurado

#### Scenario: Todos os modelos indisponíveis
- **WHEN** o modelo principal e todos os modelos de reserva falham
- **THEN** o usuário vê uma mensagem de erro e nenhuma candidatura é salva
